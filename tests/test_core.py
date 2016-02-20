"""
The tests in this file have been compiled while going through the existing
functionality.

I am planning to rewrite a big part of the back-end without losing that
functionality.
"""


from unittest.mock import MagicMock

import pytest



@pytest.fixture()
def mockapp(request):
    from lost_tracker import make_app
    mocked_model = MagicMock()
    mocked_mail_handler = MagicMock()
    app = make_app(mocked_model, mocked_mail_handler)
    return app


def test_matrix_data(mockapp):
    response = mockapp.get('/matrix')
    expected = [
        {'name': 'g1', 'p1': 'finished', 'p2': 'finished'},
        {'name': 'g2', 'p1': 'finished', 'p2': 'arrived'},
        {'name': 'g3', 'p1': 'arrived', 'p2': 'pending'},
        {'name': 'g4', 'p1': 'pending', 'p2': 'pending'},
    ]
    result = response.json()
    self.assertEqual(result, expected)

def test_list(mockapp):
    response = mockapp.get('/group')
    expected = [
        {
            'name': 'g1',
            'registration_date': '2015-01-01',
            'starting_time': '19h00',
            'direction': 'roud',
            'registration_token': 'abc'
        },
        {
            'name': 'g2',
            'registration_date': '2015-01-02',
            'starting_time': '19h00',
            'direction': 'roud',
            'registration_token': 'def'
        },
        {
            'name': 'g3',
            'registration_date': '2015-01-03',
            'starting_time': '20h00',
            'direction': 'giel',
            'registration_token': 'ghi'
        },
        {
            'name': 'g4',
            'registration_date': '2015-01-04',
            'starting_time': '',
            'direction': '',
            'registration_token': 'jkl'
        },
    ]
    result = response.json()
    self.assertEqual(result, expected)
