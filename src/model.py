import yaml

import util


class Address(yaml.YAMLObject):
    yaml_tag = '!address'

    def line(self):
        return ', '.join(self.lines)

    def multiline(self):
        return '\\\\\n'.join(self.lines)


class Entity(yaml.YAMLObject):
    yaml_tag = '!entity'

    def __get_pronoun_part(self, idx, default):
        return self.pronoun.split('/')[idx] if self.pronoun else default

    def pronoun_subject(self):
        return self.__get_pronoun_part(0, 'they')

    def pronoun_object(self):
        return self.__get_pronoun_part(1, 'them')

    def pronoun_determiner(self):
        return self.__get_pronoun_part(2, 'their')

    def full_name(self):
        names = [self.name] if isinstance(self.name, str) else self.name
        return util.and_join(names)

    def short_name(self):
        names = [self.name] if isinstance(self.name, str) else self.name
        return util.and_join(list(map(lambda name: name.split(' ')[0], names)))


class Trip(yaml.YAMLObject):
    yaml_tag = '!trip'
