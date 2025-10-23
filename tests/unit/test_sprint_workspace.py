import shutil
from pathlib import Path

from src.utils.isolation import (
    create_sprint_workspace,
    get_previous_sprint_artifacts,
    create_final_symlink,
)


def test_create_and_previous(tmp_path: Path):
    run_dir = tmp_path / "runs" / "test-run"
    # create sprint 1
    sd1, artifacts1 = create_sprint_workspace(run_dir, 1)
    assert sd1.exists()
    assert artifacts1.exists()
    # previous for sprint 1 is None
    assert get_previous_sprint_artifacts(run_dir, 1) is None

    # create sprint 2
    sd2, artifacts2 = create_sprint_workspace(run_dir, 2)
    assert sd2.exists()
    assert artifacts2.exists()
    prev = get_previous_sprint_artifacts(run_dir, 2)
    assert prev is not None
    assert prev == artifacts1


def test_final_symlink(tmp_path: Path):
    run_dir = tmp_path / "runs" / "test-symlink"
    sd1, _ = create_sprint_workspace(run_dir, 1)
    sd2, _ = create_sprint_workspace(run_dir, 2)
    link = create_final_symlink(run_dir, 2)
    assert link.exists() or link.is_symlink()
    # on POSIX the symlink target is correct
    assert link.resolve() == sd2.resolve()
