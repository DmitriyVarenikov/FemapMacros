from interface_macro import IMacro
from femap import Femap
from base_obj import FabricEquation
from config import Configuration


# todo нет обработки ошибок
class RigidToEqual(IMacro):
    def __init__(self, api_obj: Femap):
        self._api_obj = api_obj

    def run_macro(self):
        rc, f_set = femap.select()
        rc, count_elem, elem_ids = f_set.GetArray()
        id_constraint_set = femap.create_constraint_set(Configuration.NAME_CONSTRAIN_SET)
        for id in elem_ids:
            dependent_node_id, independent_nodes_id = femap.get_node_ids(id)
            nodes = [dependent_node_id] + list(independent_nodes_id)
            data = femap.get_node_coord(nodes)
            fabric = FabricEquation(data, dependent_node_id)
            equal_obj = fabric.get_equal_obj()
            equal_obj.set_equation_per_dof(False)
            femap.create_bc_equation(id_constraint_set, equal_obj.count, equal_obj.id_nodes, equal_obj.dof,
                                     equal_obj.coeff, Configuration.COLOR_EQ, Configuration.LAYER, equal_obj.name)


if __name__ == "__main__":
    femap = Femap()
    macro = RigidToEqual(femap)
    macro.run_macro()
