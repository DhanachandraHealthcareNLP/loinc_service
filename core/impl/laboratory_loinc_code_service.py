import copy
import logging
from typing import Dict, List, Set

from .classes.cache import LaboratoryLoincCodeCache
from .classes.loinc_classes import (
    LoincCodeBean,
    LoincComponent,
    LoincMethod,
    LoincSystem,
    LoincUnit,
    TextSpan,
)
from .classes.my_sql import QueryMaster, QueryMySQL


class LaboratoryLoincCodeService:
    def __init__(self, connection) -> None:
        self.query_master: QueryMaster = QueryMaster()
        self.query_my_sql: QueryMySQL = QueryMySQL(connection=connection)

        self.unit_property_map: Dict[str, str] = dict()
        self.unit_scale_map: Dict[str, str] = dict()
        self.system_set: Set[str] = set()
        self.method_set: Set[str] = set()
        self.cui_component_map: Dict[int, Set[str]] = dict()

        self.laboratory_loinc_code_cache = LaboratoryLoincCodeCache()

        self.init_loinc_service(connection=connection)

    def init_loinc_service(self, connection):
        """
        Initializes certain functions that will be required to proccess Laboratory Loinc Codes.

        :param connection: MySQL connection.
        :returns: None.
        """
        try:
            self._load_unit_to_property_and_scale_map(connection)
            self._load_unique_system_and_method_set(connection)
            self._load_cui_to_component_map(connection)
        except Exception as err:
            logging.info(f"==> Error : {err}")
            return

    def _load_unit_to_property_and_scale_map(self, connection):
        """
        Loads the unit_to_property_and_scale dictionary.

        :param connection: MySQL connection.
        :returns: None.
        """
        statement = connection.cursor(dictionary=True)

        unit_property_set_map = dict()
        unit_scale_set_map = dict()

        try:
            statement.execute(self.query_master.unit_to_property_and_scale_map_query)

            for res in statement:
                unit = res.get("example_units").strip().lower()
                property = res.get("property").strip()
                scale = res.get("scale_typ").strip()

                if unit in unit_property_set_map.keys():
                    unit_property_set_map[unit].add(property)
                else:
                    property_set = set()
                    property_set.add(property)
                    unit_property_set_map[unit] = property_set

                if unit in unit_scale_set_map.keys():
                    unit_scale_set_map[unit].add(scale)
                else:
                    scale_set = set()
                    scale_set.add(scale)
                    unit_scale_set_map[unit] = scale_set

            for key, value in unit_property_set_map.items():
                self.unit_property_map.update({key: self._get_seperate_string(value)})

            for key, value in unit_scale_set_map.items():
                self.unit_scale_map.update({key: self._get_seperate_string(value)})

            statement.close()

        except Exception as err:
            statement.close()
            return

    def _load_cui_to_component_map(self, connection):
        """
        Loads the cui_to_component dictionary.

        :param connection: MySQL connection.
        :returns: None.
        """
        statement = connection.cursor(dictionary=True)

        statement.execute(self.query_master.component_to_cui_list_query)

        for rs in statement:
            component = rs.get("component").strip()
            cuis = rs.get("cui_list")

            component = component.replace("'", "\\'")
            cuis = cuis.strip().replace("[", "").replace("]", "")
            cui_list = cuis.split(",")

            for cui in cui_list:
                cui = cui.strip()
                cui_int = int(cui)
                if cui_int in self.cui_component_map.keys():
                    self.cui_component_map[cui_int].add(component)
                else:
                    component_set = set()
                    component_set.add(component)
                    self.cui_component_map.update({cui_int: component_set})

        statement.close()

    def _load_unique_system_and_method_set(self, connection):
        """
        Loads the unique_system_and_method dictionary.

        :param connection: MySQL connection.
        :returns: None.
        """

        try:
            statement1 = connection.cursor(dictionary=True)
            statement1.execute(self.query_master.unique_system_query)
            for rs in statement1:
                system = rs.get("system")
                self.system_set.add(system.lower())

            statement1.close()

            statement2 = connection.cursor(dictionary=True)
            statement2.execute(self.query_master.unique_method_query)
            for rs in statement2:
                method = rs.get("method_typ")
                self.method_set.add(method.lower())

            statement2.close()
        except Exception as err:
            return

    def start_suggesting_code(
        self,
        component_bean: LoincComponent,
        unit_bean: LoincUnit,
        system_beans: List[LoincSystem],
        time: str,
        scale: str,
        method_beans: List[LoincMethod],
    ):
        """
        Gets the LOINC code from the given entity.

        :param component_bean: Bean containing the component details.
        :param unit_bean : Unit bean of that component.
        :param system_bean : System bean of that component.
        :time : The provided time component for the entity.
        :scale : The provided scale component for the entity.
        :method_beans : The provided method_beans component for the entity.

        :returns: Code bean with found LOINC codes, if any.
        """

        code_bean = LoincCodeBean()

        if component_bean is not None:
            component = component_bean.timex_value
            new_component = component.replace("'", "\\'")

            component_set = set()
            component_set.add(new_component)

            property = self._get_property_from_unit(unit_bean)
            present_systems = self._get_present_system(system_beans)
            time = self._get_time_from_time(time)
            scale = self._get_scale_from_unit(unit_bean)
            present_methods = self._get_present_method(method_beans)

            system = self._get_seperate_string_from_system(present_systems)
            method = self._get_seperate_string_from_method(present_methods)


            loinc_code_beans = []
            loinc_code_beans = (
                self.laboratory_loinc_code_cache.check_cache_is_available(
                    component_set,
                    property,
                    present_systems,
                    time,
                    scale,
                    present_methods,
                )
            )
            if loinc_code_beans is None:
                logging.info(f"==> Query Details = New_component: {new_component}, property: {property}, present_systems: {present_systems}, present_methods: {present_methods}, time: {time}, scale: {time}")
                new_component = self._get_seperate_string(component_set)
                query = self._generate_query(
                    new_component, property, system, time, scale, method
                )
                logging.info(f"==> Query: {query}")

                loinc_code_beans = self.query_my_sql.get_loinc_codes(query=query)
                self.laboratory_loinc_code_cache.add_into_cache(
                    loinc_code_beans,
                    component_set,
                    property,
                    present_systems,
                    time,
                    scale,
                    present_methods,
                )

            if len(loinc_code_beans) != 0:
                logging.info(f"==> Loinc codes found !, extracting evidence and returning 1st item: {loinc_code_beans}")
                code_bean = copy.deepcopy(loinc_code_beans[0])
                self._extract_evidence_from_query(
                    code_bean,
                    component_bean,
                    unit_bean,
                    property,
                    present_systems,
                    present_methods,
                )

            else:
                logging.info(f"==> Loinc code not found, trying other methods ...")
                component_cuis = component_bean.cui_set
                if component_cuis is not None and len(component_cuis) > 0:
                    for cui in component_cuis:
                        cui = int(cui)
                        if cui in self.cui_component_map.keys():
                            component_set = self.cui_component_map[cui]
                            loinc_code_beans = self.laboratory_loinc_code_cache.check_cache_is_available(
                                component_set,
                                property,
                                present_systems,
                                time,
                                scale,
                                present_methods,
                            )

                            if loinc_code_beans is None:
                                new_component = self._get_seperate_string(component_set)
                                logging.info(f"==> For CUI: {str(cui)}, Query Details = New_component: {new_component}, property: {property}, present_systems: {present_systems}, present_methods: {present_methods}, time: {time}, scale: {time}")
                                query = self._generate_query(
                                    new_component, property, system, time, scale, method
                                )
                                logging.info(f"==> Query: {query}")
                                
                                loinc_code_beans = self.query_my_sql.get_loinc_codes(
                                    query=query
                                )

                                self.laboratory_loinc_code_cache.add_into_cache(
                                    loinc_code_beans,
                                    component_set,
                                    property,
                                    present_systems,
                                    time,
                                    scale,
                                    present_methods,
                                )

                            if len(loinc_code_beans) != 0:
                                logging.info(f"==> Loinc codes found !, extracting evidence and returning 1st item: {loinc_code_beans}")
                                code_bean = copy.deepcopy(loinc_code_beans[0])
                                self._extract_evidence_from_query(
                                    code_bean,
                                    component_bean,
                                    unit_bean,
                                    property,
                                    present_systems,
                                    present_methods,
                                )
                            else : 
                                logging.info(f"==>Loinc codes not found.")

        return code_bean

    def _get_present_system(self, system_beans: List[LoincSystem]):
        """
        Get the present system from system beans.

        :param system_beans: List of system beans.
        :returns: system if the system is present in the system set else None.
        """

        if system_beans is not None or len(system_beans) != 0:
            new_system = []
            for sys_bean in system_beans:
                system = sys_bean.timexValue.lower()
                if system in self.system_set:
                    new_system.append(sys_bean)
            return new_system
        return None

    def _get_present_method(self, method_beans: List[LoincMethod]):
        """
        Get the present method from system beans.

        :param method_beans: List of system beans.
        :returns: Returns the method if the mthod is present in the method set else None.
        """

        if method_beans is not None and len(method_beans) != 0:
            new_methods = []
            for met_bean in method_beans:
                method = met_bean.timexValue.strip().lower()
                if method in self.method_set:
                    new_methods.append(met_bean)
            return new_methods
        return None

    def _get_time_from_time(self, time: str):
        """
        Get the present time.

        :param time: The time.
        :returns: "Pt" if the time is None else None.
        """

        return "Pt" if time is None else None

    def _get_property_from_unit(self, unit_bean: LoincUnit):
        """
        Get the present unit from unit bean.

        :param unit_bean: Unit bean.
        :returns: Returns the timeXValue of the unitbean if it is present in the unit_property_set else None.
        """

        return (
            self.unit_property_map.get(unit_bean.timexValue.strip().lower())
            if unit_bean is not None
            else None
        )

    def _get_scale_from_unit(self, unit_bean: LoincUnit):
        """
        Get the present scale from unit bean.

        :param unit_bean: Unit bean.
        :returns: Returns the timeXValue of the unitbean if it is present in the unit_scale_set else None.
        """

        if unit_bean is not None:
            return self.unit_scale_map.get(unit_bean.timexValue.strip().lower())
        return None

    def _get_seperate_string_from_system(self, system_beans: List[LoincSystem]):
        """
        Get the present string from system beans.

        :param system_beans: Unit bean.
        :returns: Returns the timeXValue of the sysbean if it is present.
        """

        data = None
        if system_beans is not None and len(system_beans) != 0:
            data = ""
            for sysbean in system_beans:
                data += "'" + sysbean.timexValue + "',"
            data = data[0 : len(data) - 1]

        return data

    def _get_seperate_string_from_method(self, method_beans: List[LoincMethod]):
        """
        Get the seperate unit from method beans.

        :param method_beans: Unit bean.
        :returns: Returns the timeXValue of the sys_bean if it is present.
        """

        data = None
        if method_beans is not None and len(method_beans) != 0:
            data = ""
            for sysbean in method_beans:
                data += "'" + sysbean.timexValue + "',"
            data = data[0 : len(data) - 1]

        return data

    def _get_seperate_string(self, set_item: Set[str]):
        """
        Get the set_item.

        :param set_item: Set of all the .
        :returns: Returns the data from the set_item.
        """

        data = ""
        for s in set_item:
            data += "'" + s + "',"
        data = data[0 : len(data) - 1]
        return data

    def _generate_query(
        self,
        component: str,
        property: str,
        system: str,
        time: str,
        scale: str,
        method: str,
    ):
        """
        Generate the query given the other details.

        :param component: Present component.
        :param property: Present property.
        :param system: Present system.
        :param time: Present time.
        :param scale: Present scale.
        :param method: Present method.

        :returns: The query from the given parameters.
        """

        query = self.query_master.get_loinc_laboratory_data
        if component is not None:
            query = query + " and component in (" + component + ")"
        if property is not None:
            query = query + " and property in (" + property + ")"
        if system is not None:
            query = query + " and `system` in (" + system + ")"
        if time is not None:
            query = query + " and time_aspct='" + time + "'"
        if scale is not None:
            query = query + " and scale_typ in (" + scale + ")"
        if method is not None:
            query = query + " and method_typ in (" + method + ")"
        if query is not None:
            query = (
                query
                + " order by common_test_rank,common_order_rank,common_si_test_rank;"
            )

        return query

    def _extract_evidence_from_query(
        self,
        code_bean: LoincCodeBean,
        component_bean: LoincComponent,
        unit_bean: LoincUnit,
        property: str,
        present_systems: List[LoincSystem],
        present_methods: List[LoincMethod],
    ):
        """
        Get the text span according to the detected loinc code bean.

        :param code_bean: Code bean containing Loinc code if found.
        :param component_bean: Component bean.
        :param unit bean: Unit bean.
        :param property: Property found.
        :param persent_systems: The systems that are found.
        :param present_methods: The methods that are found

        :returns: Returns the text span found for that loinc code for that entity.
        """

        text_spans = set()

        if component_bean is not None:
            text_span = TextSpan(
                text=component_bean.text, begin_offset=component_bean.begin
            )
            text_spans.add(text_span)

        if property is not None:
            text_span = TextSpan(text=unit_bean.text, begin_offset=unit_bean.begin)
            text_spans.add(text_span)

        if present_systems is not None and len(present_systems) != 0:
            for system in present_systems:
                if (
                    code_bean.system.strip().lower()
                    == system.timexValue.strip().lower()
                ):
                    text_span = TextSpan(text=system.text, begin_offset=system.begin)
                    text_spans.add(text_span)

        if present_methods is not None and len(present_methods) != 0:
            for method in present_methods:
                if (
                    code_bean.method_type.strip().lower()
                    == method.timexValue.strip().lower()
                ):
                    text_span = TextSpan(text=method.text, begin_offset=method.begin)
                    text_spans.add(text_span)

        code_bean.textSpans = text_spans


if __name__ == "__main__":
    componentBean = LoincComponent()
    componentBean.timex_value = "RBC"
    cuiSet = list()
    cuiSet.append(14722)
    componentBean.cui_set = cuiSet

    unitBean = LoincUnit()
    unitBean.timexValue = "mg/dL"

    systemBeans = []
    systemBean = LoincSystem()
    systemBean.timexValue = "Urine"
    systemBeans.append(systemBean)

    time = None
    scale = None

    methodBeans = []

    obj = LaboratoryLoincCodeService()
    codeBean = obj.start_suggesting_code(
        componentBean, unitBean, systemBeans, time, scale, methodBeans
    )

    print(codeBean)
