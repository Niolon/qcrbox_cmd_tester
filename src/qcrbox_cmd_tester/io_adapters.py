from abc import ABC, abstractmethod
from io import StringIO


class CIFIOAdapter(ABC):
    @abstractmethod
    def __init__(self, cif_text: str):
        pass

    @abstractmethod
    def get_entry_from_cif_block(self, entry_name: str) -> str | int | float | bool:
        pass

    @abstractmethod
    def get_loop_entry_from_cif_block(
        self, entry_name: str, row_lookup_entry_name: str, row_lookup_entry_value: str
    ) -> str | int | float | bool:
        pass


class ValueMissingError(Exception):
    pass


class PyCIFRWAdapter(CIFIOAdapter):
    def __init__(self, cif_text: str):
        from CifFile import ReadCif

        string_io = StringIO(cif_text)

        cf = ReadCif(string_io)
        block = cf.first_block()
        self.block = block

    def get_entry_from_cif_block(self, entry_name: str) -> str | int | float | bool:
        """
        Get a value from a CIF block using an entry name.

        Args:
            cif_block: The CIF block to extract the value from.
            cif_entry (str): The CIF entry to extract the value from.
        """
        if entry_name not in self.block:
            raise ValueMissingError(f"CIF entry '{entry_name}' not found in CIF block.")

        return self.block[entry_name]

    def get_loop_entry_from_cif_block(
        self, entry_name: str, row_lookup_entry_name: str, row_lookup_entry_value: str
    ) -> str | int | float | bool:
        """
        Get a value from a CIF block loop using an entry name.
        """
        if entry_name not in self.block:
            raise ValueMissingError(f"CIF entry '{entry_name}' not found in CIF block.")
        if row_lookup_entry_name not in self.block:
            raise ValueMissingError(f"CIF entry '{row_lookup_entry_name}' not found in CIF block.")
        loop = self.block.GetLoop(entry_name)
        row_index = loop[row_lookup_entry_name].index(row_lookup_entry_value)
        return loop[entry_name][row_index]
