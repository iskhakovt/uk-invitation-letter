import yaml

from .util import and_join, use_non_breaking_space


class Address(yaml.YAMLObject):
    yaml_tag = '!address'

    def __get_lines(self):
        return list(map(use_non_breaking_space, self.lines))

    def line(self):
        return ', '.join(self.__get_lines())

    def multiline(self):
        return '\\\\\n'.join(self.__get_lines())


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
        return and_join(list(map(use_non_breaking_space, names)))

    def short_name(self):
        names = [self.name] if isinstance(self.name, str) else self.name
        return and_join(list(map(lambda name: name.split(' ')[0], names)))


class Trip(yaml.YAMLObject):
    yaml_tag = '!trip'
