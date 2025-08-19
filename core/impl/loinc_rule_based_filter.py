from .classes.core_dto import EntityMentionDto
from .classes.my_sql import QueryMySQL


class LoincRuleBasedFilter:
    def filter_cuis_of_bilateral(
        self, system_entity_mention_dto: EntityMentionDto, query_mysql: QueryMySQL
    ):
        """
        Filter CUIs of bilateral. 

        :param system_entity_mention_dto: System Entity Dto.
        :param query_mysql: QueryMySQL object. 
        
        :returns: system CUI list. 
        """

        systemCuiList = system_entity_mention_dto.cui_set
        textSpanList = system_entity_mention_dto.text_set

        isBilateralFound = False

        for text in textSpanList:
            text = text.lower()
            if (
                "bilateral" in text
                or "bilaterally" in text
                or "both" in text
                or "b/l" in text
            ):
                isBilateralFound = True
                break

        if isBilateralFound:
            modifiedSystemCuiList = []
            for cui in systemCuiList:
                is_found = query_mysql.check_bilateral_in_text(cui)
                if is_found:
                    modifiedSystemCuiList.append(cui)

            if len(modifiedSystemCuiList) > 0:
                return modifiedSystemCuiList

        return systemCuiList
