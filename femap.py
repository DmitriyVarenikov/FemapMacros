import pythoncom
import PyFemap
from typing import Optional


class FemapError(Exception):
    pass


class Femap:
    def __init__(self):
        self._femap_obj = self._connection_to_femap()

    def _connection_to_femap(self) -> PyFemap.model:
        try:
            exit_obg = pythoncom.connect(PyFemap.model.CLSID)
            femap = PyFemap.model(exit_obg)
            femap.feAppMessage(0, "Python connected to Femap")
            return femap
        except Exception as exc:
            raise ConnectionError("Ошибка при подключения к Femap", exc)

    def select(self, entity_type=8):
        fset = self._femap_obj.feSet
        rc = fset.Select(entity_type, True, "Select Rigid Elements RBE3")
        return rc, fset

    def get_node_ids(self, elem_id: int) -> tuple[int, tuple[int, ...]]:
        f_elem = self._femap_obj.feElem
        f_elem.Get(elem_id)
        dependent_node_id = f_elem.Node(0)
        rc, _, independent_nodes_id, *_ = f_elem.GetNodeList(0)
        return dependent_node_id, independent_nodes_id

    def get_node_coord(self, nodes: tuple[int, ...]) -> dict[int, tuple[float, float, float]]:
        f_node = self._femap_obj.feNode
        set_nodes_id = self._femap_obj.feSet
        set_nodes_id.AddArray(len(nodes), nodes)
        rc, *_, coords = f_node.GetCoordArray(set_nodes_id.ID)
        return self._parse_get_node_coord(nodes, coords)

    def _parse_get_node_coord(self, node_ids: tuple[int, ...],
                              coords: tuple[float, ...]) -> dict[int, tuple[float, float, float]]:
        coords_new = {}
        for index, node in enumerate(sorted(node_ids)):
            temp = index * 3
            coords_new.setdefault(node, tuple(coords[temp:temp + 3]))
        return coords_new

    def get_new_index_any_set(self, any_set) -> int:
        rc, count, ids, *_ = any_set.GetTitleList(0, 0)
        if count:
            return max(ids) + 1
        return 1

    def create_constraint_set(self, name: str) -> int:
        """
        :param name:
        :return: id set
        """
        constraint_set = self._femap_obj.feBCSet
        return self._create_constraint_any_set(constraint_set, name)

    def create_definitions_set(self, name, id_constraint_set: Optional[int] = None) -> int:
        constrain_definition = self._femap_obj.feBCDefinition
        if id_constraint_set is None:
            return self._create_constraint_any_set(constrain_definition, name)
        elif id_constraint_set is not None and id_constraint_set > 0:
            raise NotImplementedError("Требует реализации")
        else:
            raise FemapError(f"Значение id < 0 {id_constraint_set=}")

    def _create_constraint_any_set(self, constrain_any_set, name) -> int:
        new_id = self.get_new_index_any_set(constrain_any_set)
        constrain_any_set.Get(new_id - 1)
        constrain_any_set.ID = new_id
        constrain_any_set.title = name
        constrain_any_set.Active = new_id
        constrain_any_set.Put(-1)
        return new_id

    def create_bc_equation(self, nSetID, nCount, vnode, vdof, vCoeff, eColor, nlayer, name):
        constrain_equation = self._femap_obj.feBCEqn
        t = self._femap_obj.feBCDefinition
        id_set = self.get_new_index_any_set(t)
        constrain_equation.PutAll(id_set, nSetID, id_set, nCount, vnode, vdof, vCoeff, eColor, nlayer)
        t.Last()
        t.title = name
        t.Put(-1)
