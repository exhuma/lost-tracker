import unittest
from mock import MagicMock

from lost_tracker.model import Group


class TestGroups(unittest.TestCase):

    def setUp(self):
        self.session = MagicMock()

    def test_create(self):
        group = Group.create('TestGroup')
        self.assertNotNone(group.inserted)

    def test_update(self):
        group = Group.create('TestGroup')
        self.session.merge(group)
        self.assertNotNone(group.inserted)


if __name__ == '__main__':
    unittest.main()
