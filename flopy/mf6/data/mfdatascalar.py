import numpy as np
from ..data import mfstructure, mfdatautil, mfdata
from collections import OrderedDict
from ..mfbase import ExtFileAction


class MFScalar(mfdata.MFData):
    """
    Provides an interface for the user to access and update MODFLOW scalar data.

    Parameters
    ----------
    sim_data : MFSimulationData
        data contained in the simulation
    structure : MFDataStructure
        describes the structure of the data
    data : list or ndarray
        actual data
    enable : bool
        enable/disable the array
    path : tuple
        path in the data dictionary to this MFArray
    dimensions : MFDataDimensions
        dimension information related to the model, package, and array

    Methods
    -------
    has_data : (layer_num : int) : bool
        Returns whether layer "layer_num" has any data associated with it.  For unlayered data do not pass in "layer".
    get_data : (layer_num : int) : ndarray
        Returns the data associated with layer "layer_num".  If "layer_num" is None, returns all data.
    set_data : (data : ndarray/list, multiplier : float, layer_num : int)
        Sets the contents of the data at layer "layer_num" to "data" with multiplier "multiplier".    For unlayered
        data do not pass in "layer_num".
    load : (first_line : string, file_handle : file descriptor, block_header : MFBlockHeader,
            pre_data_comments : MFComment) : tuple (bool, string)
        Loads data from first_line (the first line of data) and open file file_handle which is pointing to
        the second line of data.  Returns a tuple with the first item indicating whether all data was read
        and the second item being the last line of text read from the file.
    get_file_entry : (layer : int) : string
        Returns a string containing the data in layer "layer".  For unlayered data do not pass in "layer".

    See Also
    --------

    Notes
    -----

    Examples
    --------


    """
    def __init__(self, sim_data, structure, data=None, enable=True, path=None, dimensions=None):
        super(MFScalar, self).__init__(sim_data, structure, enable, path, dimensions)
        self._data_type = self.structure.data_item_structures[0].type
        self._data_storage = self._new_storage()
        if data is not None:
            self.set_data(data)

    def has_data(self):
        return self._get_storage_obj().has_data()

    def get_data(self, apply_mult=False):
        return self._get_storage_obj().get_data(apply_mult=apply_mult)

    def set_data(self, data):
        while isinstance(data, list) or isinstance(data, np.ndarray) or isinstance(data, tuple):
            data = data[0]
            if (isinstance(data, list) or isinstance(data, tuple)) and len(data) > 1:
                self._add_data_line_comment(data[1:], 0)
        self._get_storage_obj().set_data(self._get_storage_obj().convert_data(data, self._data_type,
                                                                              self.structure.data_item_structures[0]),
                                         key=self._current_key)

    def add_one(self):
        if self.structure.get_datum_type() == 'int' or self.structure.get_datum_type() == 'integer':
            if self._get_storage_obj().get_data() is None:
                self._get_storage_obj().set_data(1)
            else:
                self._get_storage_obj().set_data(self._get_storage_obj().get_data()+1)
        else:
            except_str = '{} of type {} does not support add one operation.'.format(self._data_name,
                                                                                    self.structure.get_datum_type())
            print(except_str)
            raise mfstructure.MFFileParseException(except_str)

    def get_file_entry(self, values_only=False, one_based=False, ext_file_action=ExtFileAction.copy_relative_paths):
        if self._get_storage_obj() is None or self._get_storage_obj().get_data() is None:
            return ''
        if self.structure.type == 'keyword':
            # keyword appears alone
            return '{}{}\n'.format(self._simulation_data.indent_string,
                                   self.structure.name.upper())
        elif self.structure.type == 'record':
            text_line = []
            for data_item in self.structure.data_item_structures:
                force_upper_case = data_item.ucase
                if data_item.type.lower() == 'keyword' and data_item.optional == False:
                    text_line.append(data_item.name.upper())
                else:
                    data = self._get_storage_obj().get_data()
                    if len(data) > 0:
                        text_line.append(self._get_storage_obj().to_string(self._get_storage_obj().get_data(),
                                                                           self._data_type,
                                                                           force_upper_case = force_upper_case))
            return '{}{}\n'.format(self._simulation_data.indent_string,
                                   self._simulation_data.indent_string.join(text_line))
        else:
            force_upper_case = self.structure.data_item_structures[0].ucase
            if one_based:
                assert(self.structure.type == 'integer' or self.structure.type == 'int')
                data = self._get_storage_obj().get_data() + 1
            else:
                data = self._get_storage_obj().get_data()
            # data
            if values_only:
                return '{}{}'.format(self._simulation_data.indent_string,
                                     self._get_storage_obj().to_string(data, self._data_type,
                                                                       force_upper_case = force_upper_case))
            else:
                # keyword + data
                return '{}{}{}{}\n'.format(self._simulation_data.indent_string,
                                           self.structure.name.upper(),
                                           self._simulation_data.indent_string,
                                           self._get_storage_obj().to_string(data, self._data_type,
                                                                             force_upper_case = force_upper_case))

    def load(self, first_line, file_handle, block_header, pre_data_comments=None):
        super(MFScalar, self).load(first_line, file_handle, block_header, pre_data_comments=None)

        # read in any pre data comments
        current_line = self._read_pre_data_comments(first_line, file_handle, pre_data_comments)

        arr_line = mfdatautil.ArrayUtil.split_data_line(current_line)
        # verify keyword
        index_num, aux_var_index = self._load_keyword(arr_line, 0)

        # store data
        if self.structure.type == 'record':
            index = 0

            for data_item_type in self.structure.get_data_item_types():
                if len(arr_line) <= index + 1 or data_item_type != 'keyword' or (index > 0 and
                  self.structure.data_item_structures[index].optional == True):
                    break
                index += 1

            self._get_storage_obj().set_data(self._get_storage_obj().convert_data(arr_line[index],
                                             self.structure.data_item_structures[index].type,
                                             self.structure.data_item_structures[0]), key=self._current_key)
        elif self.structure.get_datatype() == mfstructure.DataType.scalar_keyword or \
          self.structure.get_datatype() == mfstructure.DataType.scalar_keyword_transient:
            # store as true
            self._get_storage_obj().set_data(True, key=self._current_key)
        else:
            if len(arr_line) < 1 + index_num:
                except_str = 'Error reading variable "{}".  Expected data after label "{}" not found ' \
                             'at line "{}".'.format(self._data_name,
                                                    self.structure.data_item_structures[0].name.lower(),
                                                    current_line)
                print(except_str)
                raise mfstructure.MFFileParseException(except_str)

            # read next word as data
            self._get_storage_obj().set_data(self._get_storage_obj().convert_data(arr_line[index_num], self._data_type,
                                                                                  self.structure.data_item_structures[0]),
                                             key=self._current_key)
            index_num += 1

        if len(arr_line) > index_num:
            # save remainder of line as comment
            self._add_data_line_comment(arr_line[index_num:], 0)
        return [False, None]

    def _new_storage(self):
        return mfdata.DataStorage(self._simulation_data,
                                  self._data_dimensions,
                                  mfdata.DataStorageType.internal_array,
                                  mfdata.DataStructureType.scalar)

    def _get_storage_obj(self):
        return self._data_storage


class MFScalarTransient(MFScalar, mfdata.MFTransient):
    """
    Provides an interface for the user to access and update MODFLOW transient scalar data.

    Parameters
    ----------
    sim_data : MFSimulationData
        data contained in the simulation
    structure : MFDataStructure
        describes the structure of the data
    data : list or ndarray
        actual data
    enable : bool
        enable/disable the array
    path : tuple
        path in the data dictionary to this MFArray
    dimensions : MFDataDimensions
        dimension information related to the model, package, and array

    Methods
    -------
    add_transient_key : (transient_key : int)
        Adds a new transient time allowing data for that time to be stored and retrieved using the key
        "transient_key"
    add_one :(transient_key : int)
        Adds one to the data stored at key "transient_key"
    get_data : (layer_num : int, key : int) : ndarray
        Returns the data associated with layer "layer_num" during time "key".  If "layer_num" is None,
        returns all data for time "key".
    set_data : (data : ndarray/list, multiplier : float, layer_num : int, key : int)
        Sets the contents of the data at layer "layer_num" and time "key" to "data" with multiplier "multiplier".
        For unlayered data do not pass in "layer_num".
    load : (first_line : string, file_handle : file descriptor, block_header : MFBlockHeader,
            pre_data_comments : MFComment) : tuple (bool, string)
        Loads data from first_line (the first line of data) and open file file_handle which is pointing to
        the second line of data.  Returns a tuple with the first item indicating whether all data was read
        and the second item being the last line of text read from the file.
    get_file_entry : (layer : int, key : int) : string
        Returns a string containing the data in layer "layer" at time "key".  For unlayered data do not pass in "layer".

    See Also
    --------

    Notes
    -----

    Examples
    --------


    """
    def __init__(self, sim_data, structure, enable=True, path=None, dimensions=None):
        super(MFScalarTransient, self).__init__(sim_data=sim_data,
                                                structure=structure,
                                                enable=enable,
                                                path=path,
                                                dimensions=dimensions)
        self._transient_setup(self._data_storage, mfdata.DataStructureType.scalar)
        self.repeating = True

    def add_transient_key(self, key):
        super(MFScalarTransient, self).add_transient_key(key)
        self._data_storage[key] = super(MFScalarTransient, self)._new_storage()

    def add_one(self, key=0):
        self._update_record_prep(key)
        super(MFScalarTransient, self).add_one()

    def has_data(self, key=None):
        if key is None:
            data_found = False
            for sto_key in self._data_storage.keys():
                self.get_data_prep(sto_key)
                data_found = data_found or super(MFScalarTransient, self).has_data()
                if data_found:
                    break
        else:
            self.get_data_prep(key)
            data_found = super(MFScalarTransient, self).has_data()
        return data_found

    def get_data(self, key=0):
        self.get_data_prep(key)
        return super(MFScalarTransient, self).get_data()

    def set_data(self, data, key=None):
        if isinstance(data, dict) or isinstance(data, OrderedDict):
            # each item in the dictionary is a list for one stress period
            # the dictionary key is the stress period the list is for
            for key, list_item in data.items():
                self._set_data_prep(list_item, key)
                super(MFScalarTransient, self).set_data(list_item)
        else:
            self._set_data_prep(data, key)
            super(MFScalarTransient, self).set_data(data)

    def get_file_entry(self, key=None, ext_file_action=ExtFileAction.copy_relative_paths):
        if key is None:
            file_entry = []
            for sto_key in self._data_storage.keys():
                if self.has_data(sto_key):
                    self._get_file_entry_prep(sto_key)
                    file_entry.append(super(MFScalarTransient, self).get_file_entry(ext_file_action=ext_file_action))
            if file_entry > 1:
                return '\n\n'.join(file_entry)
            elif file_entry == 1:
                return file_entry[0]
            else:
                return ''
        else:
            self._get_file_entry_prep(key)
            return super(MFScalarTransient, self).get_file_entry(ext_file_action=ext_file_action)

    def load(self, first_line, file_handle, block_header, pre_data_comments=None):
        self._load_prep(first_line, file_handle, block_header, pre_data_comments)
        return super(MFScalarTransient, self).load(first_line, file_handle, pre_data_comments)

    def _new_storage(self):
        return OrderedDict()

    def _get_storage_obj(self):
        if self._current_key is None or self._current_key not in self._data_storage:
            return None
        return self._data_storage[self._current_key]
