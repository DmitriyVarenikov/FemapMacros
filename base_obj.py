from typing import Union
from enum import Enum

from itertools import chain
from config import Configuration


class StructUserObj(Enum):
    DEPENDENT = "DEPENDENT"
    INDEPENDENT = "INDEPENDENT"


# todo базовые объекти вы нести в отдельный модуль
class BaseNode:
    def __init__(self,
                 id_node: int,
                 x: float = 0.0,
                 y: float = 0.0,
                 z: float = 0.0):
        self._id = id_node
        self._x = x
        self._y = y
        self._z = z

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value: int):
        if isinstance(value, int):
            self._id = value
        else:
            raise ValueError(f"Не верный тип данных: {type(value)}")

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    @property
    def z(self):
        return self._z

    def __sub__(self, other):
        if isinstance(other, BaseNode):
            return self._x - other._x, self._y - other._y, self._z - other._z,


class RigidNode(BaseNode):

    def __init__(self,
                 id_node: int,
                 x: float = 0.0,
                 y: float = 0.0,
                 z: float = 0.0,
                 dependent: bool = False):
        super().__init__(id_node, x, y, z)
        self._dependent = dependent
        self._dof = {}

    @property
    def dependent(self):
        return self._dependent

    @dependent.setter
    def dependent(self, value: bool):
        if isinstance(value, bool):
            self._dependent = value
        else:
            raise ValueError(f"Не верный тип данных: {type(value)}")

    def get_dof(self) -> tuple[int, ...]:
        return tuple(sorted(self._dof))

    def set_dof(self, data: Union[tuple[int, ...], list[int, ...]]) -> None:
        """
        :param data: кортеж со степепенями свободы от 1 до 6, в порядке возрастания
        """
        if not isinstance(data, (tuple, list)) and not 7 > len(data) > 0 and not all(
                map(lambda v: isinstance(v, int) and 7 > v > 1, data)):
            raise ValueError(f"Не корректные данные {data=}")
        temp_dof = 0
        for dof in data:
            if dof > temp_dof:
                self._dof.setdefault(dof, None)
                temp_dof = dof
            else:
                raise ValueError(f"DOF должны быть в порядке возрастания. {data=}")

    def get_coefficient(self) -> tuple[int, ...]:
        return tuple(sorted(self._dof.values()))

    def set_coefficient(self, coeffs: Union[int, float, list[Union[int, float], ...], tuple[Union[int, float], ...]]):
        """Коэффициенты для DOF.
        Если будет передан 1 коэффициент, то он присвоится для всех заданных DOF
        :param coeffs: колличество и порядок должены соответствовать DOF
        """
        if len(self._dof) == 0:
            raise ValueError(f"Не установлены DOF")
        if not isinstance(coeffs, (int, float, list, tuple)):
            raise ValueError(f"Неправильный тип данных {type(coeffs)}")
        elif isinstance(coeffs, (list, tuple)) and len(coeffs) != len(self._dof):
            raise ValueError(f"Неверное колличество коэффициентов {len(coeffs)}, должно быть {len(self._dof)}")

        if isinstance(coeffs, (float, int)):
            for dof in self._dof:
                self._dof[dof] = coeffs
        elif isinstance(coeffs, (tuple, list)):
            for dof, coeffs in zip(self._dof, coeffs):
                self._dof[dof] = coeffs

    def __sub__(self, other):
        return sum(map(lambda value: value ** 2, super().__sub__(other))) ** 0.5


class Equation:
    def __init__(self,
                 list_obj: Union[list[RigidNode, ...], tuple[RigidNode, ...]]):
        self._struct = {StructUserObj.DEPENDENT: [],
                        StructUserObj.INDEPENDENT: []}
        self._data = list_obj
        self._parse_data()
        self._sort_obj()
        self._equation_per_dof = True

    @property
    def equation_per_dof(self):
        """В Femap в окне Editing Constraint Definition, в самом низе чек бокс -
        One Equation Per DOF(Одно уравнение на каждую степень свободы)"""
        return self.equation_per_dof

    def set_equation_per_dof(self, value: bool):
        """В Femap в окне Editing Constraint Definition, в самом низе чек бокс -
        One Equation Per DOF(Одно уравнение на каждую степень свободы)"""
        if not isinstance(value, bool):
            raise ValueError(f"Неверный тип данных {type(value)}")
        self._equation_per_dof = value

    @property
    def count(self) -> int:
        """Общее колличество уравнений ограничения"""
        if self._equation_per_dof:
            return sum(map(lambda lst: len(lst), self._struct.values()))
        return sum(map(lambda obj: len(obj.get_dof()), chain(*self._struct.values())))

    @property
    def id_nodes(self):
        if self._equation_per_dof:
            return tuple(map(lambda obj: obj.id, chain(*self._struct.values())))
        return tuple(chain.from_iterable(map(lambda obj: [obj.id] * len(obj.get_dof()), chain(*self._struct.values()))))

    @property
    def dof(self):
        if self._equation_per_dof:
            return tuple(map(lambda obj: obj.get_dof()[0], chain(*self._struct.values())))
        return tuple(chain.from_iterable(map(lambda obj: obj.get_dof(), chain(*self._struct.values()))))

    @property
    def coeff(self):
        if self._equation_per_dof:
            return tuple(map(lambda obj: obj.get_coefficient()[0], chain(*self._struct.values())))
        return tuple(chain.from_iterable(map(lambda obj: obj.get_coefficient(), chain(*self._struct.values()))))

    @property
    def name(self):
        dependent = ";".join(map(lambda obj: str(obj.id), self._struct[StructUserObj.DEPENDENT]))
        independent = ";".join(map(lambda obj: str(obj.id), self._struct[StructUserObj.INDEPENDENT]))
        return f"dependent({dependent}), independent({independent})"

    def _parse_data(self):
        if not isinstance(self._data, (list, tuple)) and not self._data:
            raise ValueError(f"Неверный тип данных {type(self._data)}")
        for obj in self._data:
            if obj.dependent:
                self._struct.get(StructUserObj.DEPENDENT).append(obj)
            else:
                self._struct.get(StructUserObj.INDEPENDENT).append(obj)

    def _sort_obj(self):
        for list_objs in self._struct.values():
            list_objs.sort(key=lambda obj: obj.id)


# todo фабрики  вынести в отдельный модуль
class FabricEquation:
    def __init__(self, data: dict, dependent_node_id: int):
        self._data = data
        self._dependent_node_id = dependent_node_id
        self._obj: dict[int, RigidNode] = self._create_rigid_node()
        self._analysis_coefficient()

    def get_equal_obj(self) -> Equation:
        return Equation(tuple(self._obj.values()))

    def _create_rigid_node(self) -> dict[int, RigidNode]:
        lst_obj = {}
        for node_id, coord in self._data.items():
            obj = RigidNode(node_id, *coord)
            if node_id == self._dependent_node_id:
                obj.dependent = True
            lst_obj.setdefault(node_id, obj)
            obj.set_dof(Configuration.DOF)
        return lst_obj

    def _analysis_coefficient(self) -> None:
        # todo неудачное решение, дать возможность задание через gui
        t = {}
        dependent_obj = self._obj.get(self._dependent_node_id)
        for node_id, obj in self._obj.items():
            if not obj.dependent:
                t.setdefault(node_id, dependent_obj - obj)
        sum_length = sum(t.values())
        for node_id, length in t.items():
            obj: RigidNode = self._obj.get(node_id)
            coefficient = length / sum_length * -1
            obj.set_coefficient(coefficient)
        self._obj.get(self._dependent_node_id).set_coefficient(Configuration.DEPEND_COEFF)


if __name__ == "__main__":
    a = RigidNode(4, 200, 20, 0)  # 4
    c = RigidNode(5, 200, 20, 33)  # 5
    b = RigidNode(3, 200, 0, 0, True)  # 3
    a.set_dof((1, 2, 3))
    b.set_dof((1, 2, 3))
    c.set_dof((1, 2, 3))
    l_a_b = a - b
    l_b_c = c - b
    a.set_coefficient(l_a_b / (l_a_b + l_b_c))
    b.set_coefficient(1)
    c.set_coefficient(l_b_c / (l_a_b + l_b_c))
    equation = Equation((a, b, c))
    equation.set_equation_per_dof(False)
