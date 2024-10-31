import unittest
from unittest.mock import patch
from datetime import datetime
from utils.utils import get_next_weekday, compute_next_wednesday

class TestUtils(unittest.TestCase):

    def test_get_next_weekday(self):
        # Test case 1: Start date is a Monday, looking for next Wednesday
        self.assertEqual(get_next_weekday('01/11/2021', 2), '03/11/2021')

        # Test case 2: Start date is a Friday, looking for next Monday
        self.assertEqual(get_next_weekday('05/11/2021', 0), '08/11/2021')

        # Test case 3: Start date is a Sunday, looking for next Sunday
        self.assertEqual(get_next_weekday('07/11/2021', 6), '14/11/2021')

        # Test case 4: Start date is a Wednesday, looking for next Wednesday
        self.assertEqual(get_next_weekday('03/11/2021', 2), '10/11/2021')

        # Test case 5: Start date is a Saturday, looking for next Friday
        self.assertEqual(get_next_weekday('06/11/2021', 4), '12/11/2021')

    @patch('utils.utils.datetime')
    def test_compute_next_wednesday(self, mock_date):
        # Test case 1: Today is Monday
        mock_date.today.return_value = datetime(2021, 11, 8)  # Monday
        mock_date.strptime = datetime.strptime 
        mock_date.strftime = datetime.strftime
        self.assertEqual(compute_next_wednesday(), '10/11/2021')

        # Test case 2: Today is Tuesday
        mock_date.today.return_value = datetime(2021, 11, 9)  # Tuesday
        mock_date.strptime = datetime.strptime 
        mock_date.strftime = datetime.strftime
        self.assertEqual(compute_next_wednesday(), '10/11/2021')

        # Test case 3: Today is Wednesday
        mock_date.today.return_value = datetime(2021, 11, 10)  # Wednesday
        mock_date.strptime = datetime.strptime 
        mock_date.strftime = datetime.strftime
        self.assertEqual(compute_next_wednesday(), '17/11/2021')

        # Test case 4: Today is Thursday
        mock_date.today.return_value = datetime(2021, 11, 11)  # Thursday
        mock_date.strptime = datetime.strptime 
        mock_date.strftime = datetime.strftime
        self.assertEqual(compute_next_wednesday(), '17/11/2021')

        # Test case 5: Today is Friday
        mock_date.today.return_value = datetime(2021, 11, 12)  # Friday
        mock_date.strptime = datetime.strptime 
        mock_date.strftime = datetime.strftime
        self.assertEqual(compute_next_wednesday(), '17/11/2021')

if __name__ == '__main__':
    unittest.main()