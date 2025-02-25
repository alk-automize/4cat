"""
Filter posts by a dates
"""
import csv
import dateutil.parser
from datetime import datetime

from backend.abstract.processor import BasicProcessor
from common.lib.helpers import UserInput

__author__ = "Dale Wahl"
__credits__ = ["Dale Wahl"]
__maintainer__ = "Dale Wahl"
__email__ = "4cat@oilab.eu"

csv.field_size_limit(1024 * 1024 * 1024)

class DateFilter(BasicProcessor):
    """
    Retain only posts between specific dates
    """
    type = "date-filter"  # job type ID
    category = "Filtering"  # category
    title = "Filter by date"  # title displayed in UI
    description = "Retains posts between given dates. This will create a new dataset."
    extension = "csv"  # extension of result file, used internally and in UI

    options = {
        "daterange": {
            "type": UserInput.OPTION_DATERANGE,
            "help": "Date range:"
        }
    }

    @classmethod
    def is_compatible_with(cls, module=None):
        """
        Allow processor on CSV files

        :param module: Dataset or processor to determine compatibility with
        """
        return module.is_top_dataset() and module.get_extension() in ("csv", "ndjson")

    def process(self):
        """
        Reads a CSV file, filtering items that match in the required way, and
        creates a new dataset containing the matching values
        """
        # Column to match
        # 'timestamp' should be a required field in all datasources
        date_column_name = 'timestamp'

        # Process inputs from user
        min_date, max_date = self.parameters.get("daterange")

        # Should not be None
        if not min_date or not max_date:
            self.dataset.update_status("No date range provided", is_final=True)
            self.dataset.finish(0)
            return

        # Convert to datetime for easy comparison
        min_date = datetime.fromtimestamp(min_date).date()
        max_date = datetime.fromtimestamp(max_date).date()
        
        # Track progress
        processed_items = 0
        invalid_dates = 0
        matching_items = 0

        # Start writer
        with self.dataset.get_results_path().open("w", encoding="utf-8", newline="") as outfile:
            writer = None


            # Loop through items
            for item in self.source_dataset.iterate_items(self):
                if not writer:
                    # First iteration, check if column actually exists
                    if date_column_name not in item.keys():
                        self.dataset.update_status("'%s' column not found in dataset" % date_column_name, is_final=True)
                        self.dataset.finish(0)
                        return

                    # initialise csv writer - we do this explicitly rather than
                    # using self.write_items_and_finish() because else we have
                    # to store a potentially very large amount of items in
                    # memory which is not a good idea
                    writer = csv.DictWriter(outfile, fieldnames=item.keys())
                    writer.writeheader()

                # Update 4CAT and user on status
                processed_items += 1
                if processed_items % 500 == 0:
                    self.dataset.update_status("Processed %i items (%i matching, %i invalid dates)" % (processed_items, matching_items, invalid_dates))
                    self.dataset.update_progress(processed_items / self.source_dataset.num_rows)

                # Attempt to parse timestamp
                item_date = dateutil.parser.parse(item.get(date_column_name))
                #except dateutil.parser.ParserError:
                
                # Only use date for comparison (not time)
                item_date = item_date.date()

                # Reject dates
                if min_date and item_date < min_date:
                    continue
                if max_date and item_date > max_date:
                    continue

                # Must be a good date!
                writer.writerow(item)
                matching_items += 1

        # Any matches?
        if matching_items == 0:
            self.dataset.update_status("No items matched your criteria", is_final=True)

        self.dataset.finish(matching_items)

    def after_process(self):
        super().after_process()

        # Request standalone
        self.create_standalone()
