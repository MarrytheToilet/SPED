import time

from webapp.jobs import JobManager


def test_submit_reuses_active_job_by_fingerprint():
    jm = JobManager()

    def slow(handle):
        time.sleep(0.05)
        return {"ok": True}

    first = jm.submit("x", "same", slow, fingerprint="same-work")
    second = jm.submit("x", "same", slow, fingerprint="same-work")

    assert second.id == first.id

    # Once the first job finishes, the same fingerprint may be submitted again.
    time.sleep(0.15)
    third = jm.submit("x", "same", slow, fingerprint="same-work")
    assert third.id != first.id
