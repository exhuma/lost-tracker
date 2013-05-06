from unittest import TestCase, main

from mock import patch, MagicMock

import lost_tracker.models as lm


class TestModel(TestCase):

    @patch('lost_tracker.models.select')
    def test_get_form_score_full(self, select_mock):
        lm.get_form_score_full()
        select_mock.assert_called_with([lm.form_scores])
        select_mock().order_by.assert_called_with(lm.form_scores.c.form_id)
        select_mock().order_by().execute.assert_called_with()

    @patch('lost_tracker.models.and_')
    def test_set_score(self, and_mock):
        def foo():
            print 1
        session = MagicMock()
        result_mock = MagicMock()
        session.query().filter().first.return_value = result_mock
        lm.GroupStation.set_score(
            session=session,
            group_id=10,
            station_id=20,
            score=30)
        #print session.mock_calls
        session.query.assert_called_with(lm.GroupStation)
        group_clause, station_clause = and_mock.mock_calls[0][1]
        self.assertEquals(group_clause.compile().params,
            {'group_id_1': 10})
        self.assertEquals(station_clause.compile().params,
            {'station_id_1': 20})
        self.assertEquals(result_mock.score, 30)


if __name__ == '__main__':
    main()
