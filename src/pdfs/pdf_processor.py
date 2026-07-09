#!/usr/bin/env python3
"""
PDF处理模块 - 统一的PDF上传、查询、下载接口

功能：
1. 上传PDF到MinerU
2. 查询处理状态
3. 下载解析结果
4. 状态管理（SQLite）
"""
import sys
import hashlib
import sqlite3
import requests
import zipfile
import time
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from settings import (
    MINERU_WEB_BASE,
    UPLOADS_DIR,
    DEFAULT_COLLECTION,
    BATCH_SIZE,
    BATCH_MAX_TOTAL_MB,
    UPLOAD_CONFIG,
    FILE_CONFIG,
    HTTP_REQUEST_TIMEOUT,
    UPLOAD_RETRY,
    UPLOAD_RETRY_BACKOFF_BASE,
    UPLOAD_RETRY_BACKOFF_MAX,
    DOWNLOAD_RETRY,
    DOWNLOAD_TIMEOUT,
    DOWNLOAD_CHUNK_SIZE,
    DOWNLOAD_RETRY_BACKOFF_BASE,
    DOWNLOAD_RETRY_BACKOFF_MAX
)
import settings


class PDFProcessor:
    """PDF处理器 - 统一管理PDF上传、查询、下载"""
    
    def __init__(self, db_path: Path = None):
        """
        初始化PDF处理器
        
        Args:
            db_path: 状态数据库路径
        """
        if db_path is None:
            db_path = Path(UPLOADS_DIR) / "pdf_state.db"
        
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        # 快照 MinerU 端点配置：在任务期间保持一致，避免设置热更新打断进行中的解析。
        # 新建实例（即新任务）会读取最新 settings。
        import settings as _st
        self.api_base = _st.MINERU_API_BASE
        self.headers = dict(_st.MINERU_HEADERS)
        self.upload_rate_per_min = getattr(_st, "MINERU_UPLOAD_RATE_PER_MIN", 50)
        self._init_db()
        # 统一论文目录（与本状态库共库），串联解析/提取/入库状态
        from src.database.catalog import PaperCatalog
        self.catalog = PaperCatalog(self.db_path)
    
    def _init_db(self):
        """初始化状态数据库"""
        from src.database.catalog import configure_connection, migrate_state_db
        conn = sqlite3.connect(self.db_path, timeout=30)
        configure_connection(conn)
        
        # PDF文件表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pdf_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL UNIQUE,
                file_hash TEXT NOT NULL,
                file_size INTEGER,
                batch_id TEXT,
                data_id TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 批次表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS batches (
                batch_id TEXT PRIMARY KEY,
                batch_index INTEGER,
                file_count INTEGER,
                status TEXT DEFAULT 'uploaded',
                access_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 下载记录表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS download_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id TEXT NOT NULL,
                data_id TEXT NOT NULL,
                filename TEXT,
                output_path TEXT,
                download_status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (batch_id) REFERENCES batches(batch_id)
            )
        """)
        
        # 创建索引
        conn.execute("CREATE INDEX IF NOT EXISTS idx_pdf_hash ON pdf_files(file_hash)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_pdf_status ON pdf_files(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_batch_status ON batches(status)")

        # 下载记录唯一约束：保证 INSERT OR REPLACE 按 (batch_id, data_id) 幂等
        try:
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_dl_unique "
                "ON download_records(batch_id, data_id)"
            )
        except sqlite3.IntegrityError:
            # 历史数据存在重复时跳过（不影响新逻辑）
            pass

        conn.commit()
        conn.close()
        migrate_state_db(self.db_path)
    
    def _get_file_hash(self, filepath: Path) -> str:
        """计算文件MD5哈希"""
        md5 = hashlib.md5()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                md5.update(chunk)
        return md5.hexdigest()
    
    def scan_new_pdfs(self, pdf_dir: Path = None) -> List[Path]:
        """
        扫描新PDF文件（智能去重）
        
        Args:
            pdf_dir: PDF目录
        
        Returns:
            新PDF文件列表
        """
        if pdf_dir is None:
            pdf_dir = settings.collection_pdf_dir(DEFAULT_COLLECTION)
        
        pdf_dir = Path(pdf_dir)
        if not pdf_dir.exists():
            print(f"❌ PDF目录不存在: {pdf_dir}")
            return []
        
        all_pdfs = list(pdf_dir.rglob("*.pdf"))
        print(f"📂 扫描目录: {pdf_dir}")
        print(f"📄 发现 {len(all_pdfs)} 个PDF文件")
        
        if not all_pdfs:
            return []
        
        new_pdfs = []
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        for pdf in all_pdfs:
            file_hash = self._get_file_hash(pdf)
            
            # 检查是否已存在
            cur.execute(
                "SELECT filename, status, batch_id FROM pdf_files WHERE file_hash = ?",
                (file_hash,)
            )
            existing = cur.fetchone()
            
            if existing:
                print(f"  ⏭️  跳过（已处理）: {pdf.name} -> {existing[0]} (status={existing[1]})")
            else:
                # 添加新记录
                file_size = pdf.stat().st_size
                cur.execute("""
                    INSERT INTO pdf_files (filename, file_hash, file_size, status)
                    VALUES (?, ?, ?, 'pending')
                """, (settings.logical_pdf_name(pdf), file_hash, file_size))
                new_pdfs.append(pdf)
                print(f"  ✅ 新PDF: {settings.logical_pdf_name(pdf)} ({file_size/1024/1024:.2f} MB)")
        
        conn.commit()
        conn.close()
        
        print(f"\n📊 统计: 新增 {len(new_pdfs)}/{len(all_pdfs)} 个PDF")
        return new_pdfs

    def build_upload_batches(self, pdfs: List[Path], max_files: int = None) -> List[List[Path]]:
        """
        按“文件数 + 总体积”双约束生成更均衡的上传批次。
        使用 first-fit decreasing，优先把大文件分散到不同批次，减少单批超时风险。
        max_files: 单批文件数上限（默认 BATCH_SIZE）；同时受 MinerU 速率上限约束，
        确保单批不超过 50 文件/分钟限制。
        """
        if not pdfs:
            return []

        cap = max_files if max_files else BATCH_SIZE
        max_files_per_batch = max(1, min(BATCH_SIZE, cap, self.upload_rate_per_min))
        max_batch_size_bytes = max(1, BATCH_MAX_TOTAL_MB) * 1024 * 1024

        size_pairs: List[tuple[Path, int]] = []
        for pdf in pdfs:
            try:
                size_pairs.append((pdf, pdf.stat().st_size))
            except OSError:
                # 如果获取大小失败，按0处理，不影响主流程
                size_pairs.append((pdf, 0))

        # 大文件优先，尽量均衡分配
        size_pairs.sort(key=lambda item: item[1], reverse=True)

        batches: List[List[Path]] = []
        batch_sizes: List[int] = []

        for pdf, file_size in size_pairs:
            placed = False
            for idx, batch in enumerate(batches):
                next_count = len(batch) + 1
                next_size = batch_sizes[idx] + file_size
                if next_count <= max_files_per_batch and next_size <= max_batch_size_bytes:
                    batch.append(pdf)
                    batch_sizes[idx] = next_size
                    placed = True
                    break

            if not placed:
                batches.append([pdf])
                batch_sizes.append(file_size)

        print(
            f"📦 批次规划完成: {len(pdfs)} 个文件 -> {len(batches)} 个批次 "
            f"(每批最多 {max_files_per_batch} 文件, {BATCH_MAX_TOTAL_MB} MB)"
        )
        for idx, (batch, total_size) in enumerate(zip(batches, batch_sizes), 1):
            print(f"  批次 {idx}: {len(batch)} 文件, {total_size / 1024 / 1024:.2f} MB")

        return batches
    
    def upload_batch(self, pdfs: List[Path], batch_index: int = 0) -> Optional[str]:
        """
        上传一批PDF到MinerU
        
        Args:
            pdfs: PDF文件列表
            batch_index: 批次索引
        
        Returns:
            batch_id 或 None
        """
        if not pdfs:
            print("⚠️ 没有PDF文件需要上传")
            return None

        if len(pdfs) > self.upload_rate_per_min:
            print(f"⚠️ 单批 {len(pdfs)} 文件超过速率上限 {self.upload_rate_per_min}/min，已截断")
            pdfs = pdfs[: self.upload_rate_per_min]
        
        print(f"\n🚀 上传批次 {batch_index + 1}：{len(pdfs)} 个文件")
        
        # 准备文件信息
        files_data = []
        for idx, pdf in enumerate(pdfs):
            try:
                record_name = settings.logical_pdf_name(pdf)
            except ValueError:
                record_name = pdf.name
            filename = pdf.name
            base_name = pdf.stem
            
            # 限制data_id长度
            if len(base_name) > 60:
                base_name = base_name[:60]
            
            data_id = f"b{batch_index+1}_{idx+1}_{base_name}"
            
            files_data.append({
                "name": filename,
                "record_name": record_name,
                "data_id": data_id,
                **FILE_CONFIG
            })
        
        # 申请上传URL（带重试）。429 速率限制单独计数，不消耗常规重试预算。
        try:
            result = None
            attempt = 0
            rate_waits = 0
            max_rate_waits = 10
            while attempt < max(1, UPLOAD_RETRY):
                try:
                    response = requests.post(
                        f"{self.api_base}/file-urls/batch",
                        headers=self.headers,
                        json={
                            **UPLOAD_CONFIG,
                            "files": files_data,
                        },
                        timeout=HTTP_REQUEST_TIMEOUT
                    )
                    if response.status_code == 200:
                        candidate = response.json()
                        if candidate.get("code") == 0:
                            result = candidate
                            break
                        print(f"⚠️ 申请上传URL失败：{candidate.get('msg', '未知错误')}")
                    elif response.status_code == 429:
                        # 触发 MinerU 速率限制：尊重 Retry-After，否则退避一整分钟。
                        # 不计入 attempt，仅受 max_rate_waits 上限保护，避免被偶发限速饿死批次。
                        if rate_waits >= max_rate_waits:
                            print("❌ 速率限制持续过久，放弃该批次")
                            break
                        rate_waits += 1
                        ra = response.headers.get("Retry-After")
                        wait = int(ra) if (ra and ra.isdigit()) else 65
                        print(f"⚠️ 命中速率限制(429)，等待 {wait} 秒后重试...({rate_waits}/{max_rate_waits})")
                        time.sleep(wait)
                        continue
                    else:
                        print(f"⚠️ 申请上传URL失败：HTTP {response.status_code}")
                        if response.text:
                            print(response.text[:300])
                except Exception as e:
                    print(f"⚠️ 申请上传URL异常：{str(e)[:120]}")

                attempt += 1
                if attempt < max(1, UPLOAD_RETRY):
                    delay = min(UPLOAD_RETRY_BACKOFF_MAX, UPLOAD_RETRY_BACKOFF_BASE ** attempt)
                    print(f"  ⏳ 等待 {delay} 秒后重试...")
                    time.sleep(delay)

            if not result:
                print("❌ 申请上传URL失败：超过最大重试次数")
                return None

            batch_id = result["data"]["batch_id"]
            file_urls = result["data"]["file_urls"]
            
            print(f"📦 获得批次ID: {batch_id}")
            
            # 上传文件
            success_count = 0
            for pdf, upload_url, file_data in zip(pdfs, file_urls, files_data):
                print(f"  上传: {pdf.name} ... ", end='', flush=True)
                
                uploaded = False
                for attempt in range(max(1, UPLOAD_RETRY)):
                    try:
                        with open(pdf, 'rb') as f:
                            res = requests.put(upload_url, data=f, timeout=DOWNLOAD_TIMEOUT)

                        if res.status_code in [200, 201]:
                            success_count += 1
                            uploaded = True
                            print("✅")

                            # 更新数据库状态
                            conn = sqlite3.connect(self.db_path)
                            conn.execute("""
                                UPDATE pdf_files
                                SET batch_id = ?, data_id = ?, status = 'uploaded', 
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE filename = ?
                            """, (batch_id, file_data["data_id"], file_data["record_name"]))
                            conn.commit()
                            conn.close()
                            break

                        print(f"⚠️ HTTP {res.status_code}")
                    except Exception as e:
                        print(f"⚠️ {str(e)[:50]}")

                    if attempt < max(1, UPLOAD_RETRY) - 1:
                        delay = min(UPLOAD_RETRY_BACKOFF_MAX, UPLOAD_RETRY_BACKOFF_BASE ** (attempt + 1))
                        time.sleep(delay)

                if not uploaded:
                    print("❌ 上传失败")
            
            # 保存批次信息
            access_url = f"{MINERU_WEB_BASE}/{batch_id}"
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
                INSERT OR REPLACE INTO batches 
                (batch_id, batch_index, file_count, access_url, status)
                VALUES (?, ?, ?, ?, 'uploaded')
            """, (batch_id, batch_index, len(pdfs), access_url))
            conn.commit()
            conn.close()
            
            print(f"\n✅ 批次上传完成: {success_count}/{len(pdfs)} 成功")
            print(f"🔗 访问地址: {access_url}")
            
            return batch_id
            
        except Exception as e:
            print(f"\n❌ 上传失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def check_batch_status(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """
        查询批次处理状态
        
        Args:
            batch_id: 批次ID
        
        Returns:
            状态信息字典
        """
        print(f"\n🔍 查询批次: {batch_id}")
        
        url = f"{self.api_base}/extract-results/batch/{batch_id}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=HTTP_REQUEST_TIMEOUT)
            
            if response.status_code != 200:
                print(f"❌ 查询失败：HTTP {response.status_code}")
                return None
            
            result = response.json()
            
            if result.get("code") != 0:
                print(f"❌ 查询失败：{result.get('msg', '未知错误')}")
                return None
            
            data = result["data"]
            extract_results = data.get("extract_result", [])
            
            # 统计状态
            total = len(extract_results)
            done = sum(1 for item in extract_results if item.get("state") == "done")
            processing = sum(1 for item in extract_results if item.get("state") in ["processing", "waiting"])
            failed = sum(1 for item in extract_results if item.get("state") == "failed")
            
            print(f"📊 批次状态:")
            print(f"  总文件数: {total}")
            print(f"  ✅ 已完成: {done}")
            print(f"  ⏳ 处理中: {processing}")
            print(f"  ❌ 失败: {failed}")
            
            if done == total and total > 0:
                print(f"  🎉 批次已全部完成！")
            elif total > 0:
                progress = done / total * 100
                print(f"  📈 进度: {progress:.1f}%")
            
            # 更新数据库状态
            conn = sqlite3.connect(self.db_path)
            status = 'completed' if done == total else 'processing'
            conn.execute("""
                UPDATE batches
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE batch_id = ?
            """, (status, batch_id))
            conn.commit()
            conn.close()
            
            return {
                "batch_id": batch_id,
                "total": total,
                "done": done,
                "processing": processing,
                "failed": failed,
                "all_done": done == total,
                "results": extract_results
            }
            
        except Exception as e:
            print(f"❌ 查询异常: {e}")
            return None
    
    def download_batch(self, batch_id: str, output_dir: Path = None) -> Dict[str, Any]:
        """
        下载批次处理结果
        
        Args:
            batch_id: 批次ID
            output_dir: 输出目录
        
        Returns:
            下载结果统计
        """
        if output_dir is None:
            output_dir = settings.collection_parsed_dir(DEFAULT_COLLECTION)
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n📥 下载批次: {batch_id}")
        print(f"📁 输出目录: {output_dir}")
        
        # 获取批次结果
        status = self.check_batch_status(batch_id)
        if not status:
            return {"success": False, "error": "获取批次状态失败"}
        
        if status["done"] == 0:
            print(f"\n⚠️ 批次中没有已完成的文件")
            return {"success": False, "error": "没有已完成的文件"}
        
        extract_results = status["results"]
        
        success_count = 0
        failed_count = 0
        skipped_count = 0
        
        for item in extract_results:
            data_id = item.get("data_id", "unknown")
            filename = item.get("file_name", "unknown.pdf")
            state = item.get("state", "unknown")
            zip_url = item.get("full_zip_url", "")
            
            print(f"\n📄 {filename}")
            print(f"  状态: {state}")
            
            if state != "done":
                print(f"  ⏭️  跳过（未完成）")
                skipped_count += 1
                continue
            
            if not zip_url:
                print(f"  ⚠️ 跳过（无下载链接）")
                skipped_count += 1
                continue
            
            # 检查是否已下载（并校验解析结果有效，避免把坏结果当成功跳过）
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute("""
                SELECT output_path FROM download_records
                WHERE batch_id = ? AND data_id = ? AND download_status = 'completed'
            """, (batch_id, data_id))
            existing = cur.fetchone()
            conn.close()

            if existing and Path(existing[0]).exists():
                ok, char_count = self._validate_parsed_dir(existing[0])
                if ok:
                    print(f"  ✅ 已下载: {existing[0]}")
                    # 确保统一目录同步（幂等）
                    self.catalog.mark_parsed(
                        paper_id=Path(existing[0]).name,
                        parsed_dir=existing[0],
                        char_count=char_count,
                        batch_id=batch_id,
                        mineru_data_id=data_id,
                        source_pdf=filename,
                    )
                    success_count += 1
                    continue
                print(f"  ♻️  已有结果无效，重新下载")

            # 下载 + 安全解压 + 校验 + 记账
            print(f"  ⬇️ 下载并解析中...")
            result = self._download_and_extract(
                batch_id=batch_id,
                data_id=data_id,
                filename=filename,
                zip_url=zip_url,
                output_dir=output_dir,
            )
            if result["success"]:
                print(f"  ✅ 完成: {result['output_path']}")
                success_count += 1
            else:
                print(f"  ❌ {result['error']}")
                failed_count += 1
        
        # 更新批次状态
        conn = sqlite3.connect(self.db_path)
        if success_count == len(extract_results):
            batch_status = 'completed'
        elif success_count > 0:
            batch_status = 'partial'
        else:
            batch_status = 'uploaded'
        
        conn.execute("""
            UPDATE batches
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE batch_id = ?
        """, (batch_status, batch_id))
        conn.commit()
        conn.close()
        
        print(f"\n{'='*60}")
        print(f"📊 下载统计:")
        print(f"  ✅ 成功: {success_count}")
        print(f"  ❌ 失败: {failed_count}")
        print(f"  ⏭️  跳过: {skipped_count}")
        print(f"{'='*60}")
        
        return {
            "success": success_count > 0,
            "success_count": success_count,
            "failed_count": failed_count,
            "skipped_count": skipped_count,
            "total": len(extract_results)
        }
    
    def _download_file(self, url: str, save_path: Path, retry: int = None) -> bool:
        """下载文件（带重试）"""
        if retry is None:
            retry = DOWNLOAD_RETRY
        
        for attempt in range(retry):
            try:
                response = requests.get(url, timeout=DOWNLOAD_TIMEOUT, stream=True)
                if response.status_code == 200:
                    with open(save_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
                            if chunk:
                                f.write(chunk)
                    return True
                else:
                    if attempt < retry - 1:
                        delay = min(
                            DOWNLOAD_RETRY_BACKOFF_MAX,
                            DOWNLOAD_RETRY_BACKOFF_BASE ** (attempt + 1)
                        )
                        time.sleep(delay)
            except Exception:
                if attempt < retry - 1:
                    delay = min(
                        DOWNLOAD_RETRY_BACKOFF_MAX,
                        DOWNLOAD_RETRY_BACKOFF_BASE ** (attempt + 1)
                    )
                    time.sleep(delay)
        
        return False
    
    def _unzip_file(self, zip_path: Path, extract_to: Path) -> bool:
        """安全解压ZIP文件（拒绝绝对路径与 .. 目录穿越）"""
        extract_to = Path(extract_to).resolve()
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for member in zip_ref.namelist():
                    # 防御 zip-slip：解析后的目标必须仍在 extract_to 之内
                    target = (extract_to / member).resolve()
                    if not str(target).startswith(str(extract_to)):
                        print(f"  ⚠️ 跳过不安全的压缩包条目: {member}")
                        return False
                zip_ref.extractall(extract_to)
            return True
        except Exception as e:
            print(f"  解压错误: {e}")
            return False

    # ------------------------------------------------------------------
    # MinerU 下载健壮性辅助
    # ------------------------------------------------------------------
    @staticmethod
    def _safe_stem(filename: str) -> str:
        """由文件名生成安全的目录名"""
        return "".join(
            c if c.isalnum() or c in "._- " else "_" for c in Path(filename).stem
        ).strip() or "unnamed"

    def _resolve_paper_dir(
        self, output_dir: Path, filename: str, batch_id: str, data_id: str
    ) -> Path:
        """
        生成解析结果目录，避免不同 PDF（同名 stem）互相覆盖。

        若目标目录已被「不同 data_id」的下载记录占用，则追加 data_id 短哈希后缀。
        """
        output_dir = Path(output_dir)
        base = self._safe_stem(filename)
        candidate = output_dir / base

        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT data_id FROM download_records WHERE output_path = ?",
                (str(candidate),),
            )
            owners = {row[0] for row in cur.fetchall()}
        finally:
            conn.close()

        # 目录没被占用，或正是本 data_id 占用 -> 直接用
        if not owners or owners == {data_id}:
            return candidate

        # 目录被其它 data_id 占用 -> 追加短哈希避免覆盖
        suffix = hashlib.md5(data_id.encode()).hexdigest()[:6]
        return output_dir / f"{base}__{suffix}"

    @staticmethod
    def _validate_parsed_dir(paper_dir: Path) -> Tuple[bool, int]:
        """校验解析目录是否含有效 full.md，返回 (是否有效, 字符数)"""
        full_md = Path(paper_dir) / "full.md"
        if not full_md.exists() or full_md.stat().st_size == 0:
            return False, 0
        try:
            text = full_md.read_text(encoding="utf-8")
        except Exception:
            return False, 0
        if not text.strip():
            return False, 0
        return True, len(text)

    def _record_download_success(
        self, batch_id: str, data_id: str, filename: str,
        paper_dir: Path, char_count: int
    ) -> None:
        """写入下载成功记录、更新 pdf_files、并更新统一论文目录"""
        conn = sqlite3.connect(self.db_path)
        try:
            row = conn.execute(
                "SELECT filename FROM pdf_files WHERE data_id = ?",
                (data_id,),
            ).fetchone()
            source_pdf = row[0] if row else filename
            conn.execute(
                """
                INSERT OR REPLACE INTO download_records
                (batch_id, data_id, filename, output_path, download_status)
                VALUES (?, ?, ?, ?, 'completed')
                """,
                (batch_id, data_id, source_pdf, str(paper_dir)),
            )
            conn.execute(
                """
                UPDATE pdf_files
                SET status = 'downloaded', updated_at = CURRENT_TIMESTAMP
                WHERE data_id = ? OR filename = ?
                """,
                (data_id, filename),
            )
            conn.commit()
        finally:
            conn.close()

        # 统一论文目录：paper_id 沿用解析目录名（与提取/入库的 paper_id 对齐）
        self.catalog.mark_parsed(
            paper_id=Path(paper_dir).name,
            parsed_dir=str(paper_dir),
            char_count=char_count,
            batch_id=batch_id,
            mineru_data_id=data_id,
            source_pdf=source_pdf,
        )

    def _record_download_failure(
        self, batch_id: str, data_id: str, filename: str,
        paper_dir: Path, error: str
    ) -> None:
        """记录下载/解析失败到统一论文目录"""
        conn = sqlite3.connect(self.db_path)
        try:
            row = conn.execute(
                "SELECT filename FROM pdf_files WHERE data_id = ?",
                (data_id,),
            ).fetchone()
            source_pdf = row[0] if row else filename
            conn.execute(
                "UPDATE pdf_files SET status='failed', updated_at=CURRENT_TIMESTAMP WHERE data_id=? OR filename=?",
                (data_id, filename),
            )
            conn.commit()
        finally:
            conn.close()
        self.catalog.mark_parse_failed(
            paper_id=Path(paper_dir).name,
            error=error,
            batch_id=batch_id,
            mineru_data_id=data_id,
            source_pdf=source_pdf,
        )

    def _download_and_extract(
        self, batch_id: str, data_id: str, filename: str,
        zip_url: str, output_dir: Path
    ) -> Dict[str, Any]:
        """
        完整处理单个文件：定位目录 -> 下载 -> 安全解压 -> 校验 full.md -> 记账。

        返回 {"success": bool, "output_path"/"error": ...}
        """
        paper_dir = self._resolve_paper_dir(output_dir, filename, batch_id, data_id)
        paper_dir.mkdir(parents=True, exist_ok=True)
        zip_path = paper_dir / "mineru_output.zip"

        if not self._download_file(zip_url, zip_path):
            self._record_download_failure(batch_id, data_id, filename, paper_dir, "下载失败")
            return {"success": False, "error": "下载失败"}

        if not self._unzip_file(zip_path, paper_dir):
            self._record_download_failure(batch_id, data_id, filename, paper_dir, "解压失败")
            return {"success": False, "error": "解压失败"}

        # 删除ZIP节省空间
        try:
            zip_path.unlink()
        except OSError:
            pass

        # 校验 MinerU 解析结果（常见 bug：zip 内缺少/为空的 full.md）
        ok, char_count = self._validate_parsed_dir(paper_dir)
        if not ok:
            self._record_download_failure(
                batch_id, data_id, filename, paper_dir, "解析结果缺少有效的 full.md"
            )
            return {"success": False, "error": "解析结果缺少有效的 full.md"}

        self._record_download_success(batch_id, data_id, filename, paper_dir, char_count)
        return {"success": True, "output_path": str(paper_dir)}

    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        # PDF统计
        cur.execute("SELECT COUNT(*) FROM pdf_files")
        total_pdfs = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM pdf_files WHERE status = 'uploaded'")
        uploaded = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM pdf_files WHERE status = 'downloaded'")
        downloaded = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM pdf_files WHERE status = 'pending'")
        pending = cur.fetchone()[0]
        
        # 批次统计
        cur.execute("SELECT COUNT(*) FROM batches")
        total_batches = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM batches WHERE status = 'completed'")
        completed_batches = cur.fetchone()[0]
        
        conn.close()
        
        return {
            "total_pdfs": total_pdfs,
            "uploaded": uploaded,
            "downloaded": downloaded,
            "pending": pending,
            "total_batches": total_batches,
            "completed_batches": completed_batches
        }
    
    def list_batches(self) -> List[Dict[str, Any]]:
        """列出所有批次"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT batch_id, batch_index, file_count, status, 
                   access_url, created_at, updated_at
            FROM batches
            ORDER BY batch_index DESC
        """)
        
        batches = []
        for row in cur.fetchall():
            batches.append({
                "batch_id": row[0],
                "batch_index": row[1],
                "file_count": row[2],
                "status": row[3],
                "access_url": row[4],
                "created_at": row[5],
                "updated_at": row[6]
            })
        
        conn.close()
        return batches
    
    def download_batch_parallel(
        self, 
        batch_id: str, 
        output_dir: Path = None,
        max_workers: int = 4
    ) -> Dict[str, Any]:
        """
        并行下载批次处理结果
        
        Args:
            batch_id: 批次ID
            output_dir: 输出目录
            max_workers: 最大并行数
        
        Returns:
            下载结果统计
        """
        if output_dir is None:
            output_dir = settings.collection_parsed_dir(DEFAULT_COLLECTION)
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n📥 并行下载批次: {batch_id} (workers={max_workers})")
        print(f"📁 输出目录: {output_dir}")
        
        # 获取批次结果
        status = self.check_batch_status(batch_id)
        if not status:
            return {"success": False, "error": "获取批次状态失败"}
        
        if status["done"] == 0:
            print(f"\n⚠️ 批次中没有已完成的文件")
            return {"success": False, "error": "没有已完成的文件"}
        
        extract_results = status["results"]
        
        # 过滤出需要下载的文件
        to_download = []
        already_done = 0
        
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        for item in extract_results:
            data_id = item.get("data_id", "unknown")
            filename = item.get("file_name", "unknown.pdf")
            state = item.get("state", "unknown")
            zip_url = item.get("full_zip_url", "")
            
            if state != "done" or not zip_url:
                continue
            
            # 检查是否已下载
            cur.execute("""
                SELECT output_path FROM download_records
                WHERE batch_id = ? AND data_id = ? AND download_status = 'completed'
            """, (batch_id, data_id))
            existing = cur.fetchone()
            
            if existing and Path(existing[0]).exists() and \
                    self._validate_parsed_dir(existing[0])[0]:
                already_done += 1
                continue
            
            to_download.append({
                "batch_id": batch_id,
                "data_id": data_id,
                "filename": filename,
                "zip_url": zip_url,
                "output_dir": output_dir
            })
        
        conn.close()
        
        if not to_download:
            print(f"\n✅ 所有文件已下载完成 ({already_done}个)")
            return {
                "success": True,
                "success_count": already_done,
                "failed_count": 0,
                "skipped_count": 0,
                "total": len(extract_results)
            }
        
        print(f"\n📊 待下载: {len(to_download)}个, 已完成: {already_done}个")
        
        # 并行下载
        success_count = already_done
        failed_count = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._download_single_file, item): item 
                for item in to_download
            }
            
            for future in as_completed(futures):
                item = futures[future]
                try:
                    result = future.result()
                    if result["success"]:
                        success_count += 1
                        print(f"  ✅ {item['filename']}")
                    else:
                        failed_count += 1
                        print(f"  ❌ {item['filename']}: {result.get('error', '未知错误')}")
                except Exception as e:
                    failed_count += 1
                    print(f"  ❌ {item['filename']}: {e}")
        
        # 更新批次状态
        conn = sqlite3.connect(self.db_path)
        total_expected = len(extract_results)
        if success_count == total_expected:
            batch_status = 'completed'
        elif success_count > 0:
            batch_status = 'partial'
        else:
            batch_status = 'uploaded'
        
        conn.execute("""
            UPDATE batches
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE batch_id = ?
        """, (batch_status, batch_id))
        conn.commit()
        conn.close()
        
        print(f"\n{'='*60}")
        print(f"📊 下载统计:")
        print(f"  ✅ 成功: {success_count}")
        print(f"  ❌ 失败: {failed_count}")
        print(f"{'='*60}")
        
        return {
            "success": success_count > 0,
            "success_count": success_count,
            "failed_count": failed_count,
            "skipped_count": 0,
            "total": len(extract_results)
        }
    
    def _download_single_file(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """下载单个文件（用于并行下载）"""
        try:
            return self._download_and_extract(
                batch_id=item["batch_id"],
                data_id=item["data_id"],
                filename=item["filename"],
                zip_url=item["zip_url"],
                output_dir=item["output_dir"],
            )
        except Exception as e:
            return {"success": False, "error": str(e)}


# ==================== 便捷函数 ====================

def quick_upload(pdf_dir: Path = None, collection: str = None) -> List[str]:
    """
    快速上传：扫描新PDF并上传
    
    Returns:
        batch_id列表
    """
    processor = PDFProcessor()
    if pdf_dir is None:
        pdf_dir = settings.collection_pdf_dir(collection or DEFAULT_COLLECTION)
    
    # 扫描新PDF
    new_pdfs = processor.scan_new_pdfs(pdf_dir)
    
    if not new_pdfs:
        print("\n✅ 没有新PDF需要上传")
        return []
    
    # 分批上传（按大小+数量均衡）
    batch_ids = []
    planned_batches = processor.build_upload_batches(new_pdfs)

    for i, batch_pdfs in enumerate(planned_batches):
        batch_id = processor.upload_batch(batch_pdfs, i)
        if batch_id:
            batch_ids.append(batch_id)
    
    print(f"\n🎉 上传完成！共 {len(batch_ids)} 个批次")
    for bid in batch_ids:
        print(f"  📦 {bid}")
    
    return batch_ids


def quick_status(batch_id: str = None) -> None:
    """
    快速查询：查询批次或所有批次的状态
    
    Args:
        batch_id: 批次ID，None则查询所有
    """
    processor = PDFProcessor()
    
    if batch_id:
        # 查询单个批次
        processor.check_batch_status(batch_id)
    else:
        # 查询所有批次
        batches = processor.list_batches()
        
        if not batches:
            print("⚠️ 没有找到任何批次")
            return
        
        print(f"📋 共 {len(batches)} 个批次\n")
        
        for batch in batches:
            print(f"\n📦 批次 {batch['batch_index'] + 1}: {batch['batch_id']}")
            print(f"  文件数: {batch['file_count']}")
            print(f"  状态: {batch['status']}")
            print(f"  创建时间: {batch['created_at']}")
            print(f"  访问地址: {batch['access_url']}")


def quick_download(batch_id: str, output_dir: Path = None, collection: str = None) -> bool:
    """
    快速下载：下载批次结果
    
    Args:
        batch_id: 批次ID
        output_dir: 输出目录
    
    Returns:
        是否成功
    """
    processor = PDFProcessor()
    if output_dir is None:
        output_dir = settings.collection_parsed_dir(collection or DEFAULT_COLLECTION)
    result = processor.download_batch(batch_id, output_dir)
    return result.get("success", False)


def show_stats() -> None:
    """显示统计信息"""
    processor = PDFProcessor()
    stats = processor.get_statistics()
    
    print(f"\n{'='*60}")
    print(f"📊 PDF处理统计")
    print(f"{'='*60}")
    print(f"PDF文件:")
    print(f"  总数: {stats['total_pdfs']}")
    print(f"  待上传: {stats['pending']}")
    print(f"  已上传: {stats['uploaded']}")
    print(f"  已下载: {stats['downloaded']}")
    print(f"\n批次:")
    print(f"  总数: {stats['total_batches']}")
    print(f"  已完成: {stats['completed_batches']}")
    print(f"{'='*60}")


# ==================== 主函数 ====================

def main():
    """命令行主入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="PDF处理工具")
    subparsers = parser.add_subparsers(dest='action', help='操作')
    
    # upload
    upload_parser = subparsers.add_parser('upload', help='上传PDF')
    upload_parser.add_argument('--dir', type=Path, help='PDF目录')
    upload_parser.add_argument('--collection', default=None, help='主题 collection')
    
    # status
    status_parser = subparsers.add_parser('status', help='查询状态')
    status_parser.add_argument('batch_id', nargs='?', help='批次ID（可选）')
    
    # download
    download_parser = subparsers.add_parser('download', help='下载结果')
    download_parser.add_argument('batch_id', help='批次ID')
    download_parser.add_argument('--output', type=Path, help='输出目录')
    download_parser.add_argument('--collection', default=None, help='主题 collection')
    
    # stats
    stats_parser = subparsers.add_parser('stats', help='显示统计')
    
    # scan
    scan_parser = subparsers.add_parser('scan', help='扫描新PDF')
    scan_parser.add_argument('--dir', type=Path, help='PDF目录')
    scan_parser.add_argument('--collection', default=None, help='主题 collection')
    
    args = parser.parse_args()
    
    if not args.action:
        parser.print_help()
        return 1
    
    try:
        if args.action == 'upload':
            quick_upload(args.dir, args.collection)
        elif args.action == 'status':
            quick_status(args.batch_id)
        elif args.action == 'download':
            quick_download(args.batch_id, args.output, args.collection)
        elif args.action == 'stats':
            show_stats()
        elif args.action == 'scan':
            processor = PDFProcessor()
            scan_dir = args.dir or settings.collection_pdf_dir(args.collection or DEFAULT_COLLECTION)
            processor.scan_new_pdfs(scan_dir)
        
        return 0
    
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        return 130
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
