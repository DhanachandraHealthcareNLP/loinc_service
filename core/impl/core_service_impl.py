from .classes.core_dto import *
from typing import Dict, List, Set


class CoreServiceImplementation:
    def get_status_data(self, cDoc) -> Dict[Span, int]:
        status_boundary_to_span_status = {}
        if "status" in cDoc.keys():
            for item in cDoc["status"]:
                dict_status = None  # TODO : look into this
                begin = None  # TODO : Look into this
                end = None  # TODO : Look into this

                new_span = Span(begin=begin, end=end)
                status_boundary_to_span_status.update({new_span: dict_status})

        return status_boundary_to_span_status

    def get_negation_data(self, cDoc) -> Dict[Span, int]:
        negation_boundary_span_to_negation_status = {}

        if "status" in cDoc.keys():
            for item in cDoc["negation"]:
                polarity = None  # TODO : look into this
                begin = None  # TODO : Look into this
                end = None  # TODO : Look into this

                negation_boundary_span_to_negation_status.update([begin, end], polarity)

        return negation_boundary_span_to_negation_status

    def get_section_data(self, cDoc):
        sec_beg_end_to_name = {}
        if "status" in cDoc.keys():
            for item in cDoc["negation"]:
                polarity = None  # TODO : look into this
                begin = None  # TODO : Look into this
                end = None  # TODO : Look into this

                new_span = Span(begin=begin, end=end)
                sec_beg_end_to_name.update({new_span: polarity})

        return sec_beg_end_to_name

    def get_crf_entity_data(self, cDoc) -> Dict[Span, CRFEntityMention]:
        """
        Get the Entity Data and fill then into the class CRFEntityMention.

        :param cDoc: NER Json data.
        :returns: Dictionary with key as the Span and the item being the Entity. 
        """

        crf_beg_end_to_crf_mention: Dict[Span, CRFEntityMention] = dict()

        # Iterate through all the entities in the "entities" key in cDoc
        for entity in cDoc["entities"]:
            cui_list = []
            for it in entity["metadata"]["normalization"]:
                for cui in it["cuis"]:
                    cui_list += [int(c.strip().split("C")[1]) for c in cui.split(",")]
            tui_list = []
            for it in entity["metadata"]["normalization"]:
                for tui in it["tuis"]:
                    tui_list += [int(t.strip().split("T")[1]) for t in tui.split(",")]
            sui_list = []
            for it in entity["metadata"]["normalization"]:
                for sui in it["suis"]:
                    sui_list += [int(s.strip().split("S")[1]) for s in sui.split(",")]
            crf_entity = CRFEntityMention(
                id=int(entity["id"]),
                begin=[int(it["begin"]) for it in entity["textSpan"]][0],
                end=[int(it["end"]) for it in entity["textSpan"]][-1],
                entity_type=entity["type"],
                confidence=float(entity["confidence"]),
                status=entity["status"],
                cui_list=cui_list,
                sui_list=sui_list,
                tui_list=tui_list,
                # unit_list=[it for it in entity["metadata"]["drugData"]["unit"]],
                # dosage_list=[it for it in entity["metadata"]["drugData"]["dose"]],
                # freq_list=[it for it in entity["metadata"]["drugData"]["frequency"]],
                # form_list=[it for it in entity["metadata"]["drugData"]["form"]],
                # strength_list=[it for it in entity["metadata"]["drugData"]["strength"]],
                method_list=[it for it in entity["metadata"]["labData"]["method"]],
                system_list=[it for it in entity["metadata"]["labData"]["system"]],
                value_list=[it for it in entity["metadata"]["labData"]["value"]],
            )

            modality_list = []
            view_list = []
            pharmaceutical_list = []
            radiologyroute_list = []
            unit_list = []
            for token in cDoc["contextTokens"]:
                if int(token["begin"]) <= crf_entity.begin and crf_entity.end < int(
                    token["end"]
                ):
                    if token["type"] == "ModalityToken":
                        modality_list.append(token)
                    elif token["type"] == "ViewToken":
                        view_list.append(token)
                    elif token["type"] == "PharmaceuticalToken":
                        pharmaceutical_list.append(token)
                    elif token["type"] == "RadiologyrouteToken":
                        radiologyroute_list.append(token)
                    elif token["type"] == "UnitToken":
                        unit_list.append(token)

            crf_entity.modality_list = modality_list
            crf_entity.view_list = view_list
            crf_entity.pharmaceutical_list = pharmaceutical_list
            crf_entity.radiologyroute_list = radiologyroute_list
            crf_entity.unit_list = unit_list

            crf_beg_end_to_crf_mention.update(
                {Span(begin=crf_entity.begin, end=crf_entity.end): crf_entity}
            )

        return crf_beg_end_to_crf_mention

    def get_entity_mention_data(self, cDoc) -> Dict[Sentence, Set[EntityMentionDto]]:
        """
        Get the entity data from sentence level. 

        :param cDoc: NER JSON data.
        :returns: Dictionary with key being the sentence and the values being the entities present in the sentence. 
        """

        document = cDoc["content"]
        sent_entity_mention_map = {}
        entity_mention_dto_set = set()

        sentence_list = cDoc["sentences"]

        for sent in sentence_list:
            sent_obj = Sentence(
                begin=int(sent["begin"]),
                end=int(sent["end"]),
                sentence_num=int(sent["id"]),
            )
            ent_mention = self.get_entity_mention_of_sentence(
                sent_obj, cDoc["entities"]
            )
            sent_wise_entity_mention_dto = set()

            text = document[sent_obj.begin : sent_obj.end]
            for em in ent_mention:
                entity_mention_dto_set.add(em)
                sent_wise_entity_mention_dto.add(em)

            sent_obj.covered_text = text
            sent_entity_mention_map.update({sent_obj: sent_wise_entity_mention_dto})

        return sent_entity_mention_map

    def get_entity_mention_of_sentence(
        self, sentence_ent: Sentence, all_entities
    ) -> Set[EntityMentionDto]:
        """
        Get the entites in a sentence. 

        :param sentence_ent: Current sentence being processed.
        :returns: All the entities in the present sentence. 
        """

        # Entity List should be : "entities"

        sent_begin = sentence_ent.begin
        sent_end = sentence_ent.end
        sent_id = sentence_ent.sentence_num

        em_set = set()

        for entity in all_entities:
            ent_begin = [int(it["begin"]) for it in entity["textSpan"]][0]
            ent_end = [int(it["end"]) for it in entity["textSpan"]][-1]
            if sent_begin <= ent_begin and ent_end < sent_end:
                begin_lst = [int(it["begin"]) for it in entity["textSpan"]]
                end_lst = [int(it["end"]) for it in entity["textSpan"]]
                text_set = [it["text"] for it in entity["textSpan"]]
                cui_list = []
                for it in entity["metadata"]["normalization"]:
                    for cui in it["cuis"]:
                        cui_list += [
                            int(c.strip().split("C")[1]) for c in cui.split(",")
                        ]
                tui_list = []
                for it in entity["metadata"]["normalization"]:
                    for tui in it["tuis"]:
                        tui_list += [
                            int(t.strip().split("T")[1]) for t in tui.split(",")
                        ]
                sui_list = []
                for it in entity["metadata"]["normalization"]:
                    for sui in it["suis"]:
                        sui_list += [
                            int(s.strip().split("S")[1]) for s in sui.split(",")
                        ]
                id = entity["id"]
                possible_types = [entity["type"]]

                new_ent = EntityMentionDto(
                    id=id,
                    begin_set=begin_lst,
                    end_set=end_lst,
                    text_set=text_set,
                    cui_set=cui_list,
                    tui_set=tui_list,
                    sui_set=sui_list,
                    possible_entity_type_set=possible_types,
                )

                em_set.add(new_ent)

        return em_set
