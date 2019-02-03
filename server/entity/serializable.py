""" JSON serialization helper.
"""
import json


class Serializable(object):

    def set_attributes(self, **kwargs):
        for attr, value in kwargs.items():
            setattr(self, attr, value)

    def __repr__(self):
        return json.dumps(
            self.__dict__,
            default=self.default_serializer
        )

    @staticmethod
    def default_serializer(obj, attributes=None):
        obj_dict = obj.__dict__.copy()

        if hasattr(obj, 'PROTECTED'):
            for attr in obj.PROTECTED:
                obj_dict.pop(attr, None)

        if attributes:
            for attr in list(obj_dict.keys()):
                if attr not in attributes:
                    obj_dict.pop(attr, None)

        if hasattr(obj, 'DICT_TO_LIST'):
            for attr in obj.DICT_TO_LIST:
                if attr in obj_dict:
                    obj_dict[attr] = list(obj_dict[attr].values())

        return obj_dict

    def to_json_str(self, attributes=None):
        obj_dict = self.default_serializer(self, attributes=attributes)
        return json.dumps(
            obj_dict, sort_keys=True, indent=4,
            default=self.default_serializer
        )
