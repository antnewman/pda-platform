"""Tests for Task model."""

import pytest
from datetime import datetime

from agent_planning.core.task import Task, TaskStatus


class TestTask:
    """Tests for Task class."""

    def test_create_task(self):
        """Test creating a basic task."""
        task = Task(content="Test task")
        assert task.content == "Test task"
        assert task.status == TaskStatus.PENDING
        assert task.attempts == 0
        assert task.error is None
        assert task.result is None

    def test_mark_in_progress(self):
        """Test marking task in progress."""
        task = Task(content="Test")
        task.mark_in_progress()
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.attempts == 1

    def test_mark_completed(self):
        """Test marking task completed."""
        task = Task(content="Test")
        task.mark_completed("Done!")
        assert task.status == TaskStatus.COMPLETED
        assert task.result == "Done!"

    def test_mark_failed(self):
        """Test marking task failed."""
        task = Task(content="Test")
        task.mark_failed("Something went wrong")
        assert task.status == TaskStatus.FAILED
        assert task.error == "Something went wrong"

    def test_is_terminal(self):
        """Test terminal state detection."""
        task = Task(content="Test")
        assert not task.is_terminal

        task.mark_completed()
        assert task.is_terminal

        task2 = Task(content="Test 2")
        task2.mark_failed("Error")
        assert task2.is_terminal

    def test_to_display(self):
        """Test display formatting."""
        task = Task(content="My task")
        assert "☐" in task.to_display()

        task.mark_in_progress()
        assert "◐" in task.to_display()

        task.mark_completed()
        assert "✓" in task.to_display()

    def test_multiple_attempts(self):
        """Test attempt counting."""
        task = Task(content="Retry task")
        task.mark_in_progress()
        assert task.attempts == 1

        task.status = TaskStatus.PENDING
        task.mark_in_progress()
        assert task.attempts == 2
