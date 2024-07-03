import re
from collections.abc import Iterator

from danswer.chat.models import AnswerQuestionStreamReturn
from danswer.chat.models import CitationInfo
from danswer.chat.models import DanswerAnswerPiece
from danswer.chat.models import LlmDoc
from danswer.configs.chat_configs import STOP_STREAM_PAT
from danswer.llm.answering.models import StreamProcessor
from danswer.llm.answering.stream_processing.utils import map_document_id_order
from danswer.prompts.constants import TRIPLE_BACKTICK
from danswer.utils.logger import setup_logger


logger = setup_logger()


def in_code_block(llm_text: str) -> bool:
    count = llm_text.count(TRIPLE_BACKTICK)
    return count % 2 != 0


def extract_citations_from_stream(
    tokens: Iterator[str],
    context_docs: list[LlmDoc],
    doc_id_to_rank_map: dict[str, int],
    stop_stream: str | None = STOP_STREAM_PAT,
) -> Iterator[DanswerAnswerPiece | CitationInfo]:
    llm_out = ""
    max_citation_num = len(context_docs)
    curr_segment = ""
    cited_inds = set()
    hold = ""
    last_cited_num = None

    for raw_token in tokens:
        if stop_stream:
            next_hold = hold + raw_token
            if stop_stream in next_hold:
                break
            if next_hold == stop_stream[: len(next_hold)]:
                hold = next_hold
                continue
            token = next_hold
            hold = ""
        else:
            token = raw_token

        curr_segment += token
        llm_out += token

        citation_pattern = r"\[(\d+)\]"
        citations_found = list(re.finditer(citation_pattern, curr_segment))

        if citations_found and not in_code_block(llm_out):
            last_citation_end = 0
            for citation in citations_found:
                numerical_value = int(citation.group(1))
                if 1 <= numerical_value <= max_citation_num:
                    context_llm_doc = context_docs[numerical_value - 1]
                    target_citation_num = doc_id_to_rank_map[
                        context_llm_doc.document_id
                    ]

                    # Skip consecutive citations of the same work
                    if target_citation_num == last_cited_num:
                        start, end = citation.span()
                        curr_segment = curr_segment[:start] + curr_segment[end:]
                        continue

                    link = context_llm_doc.link

                    # Replace the citation in the current segment
                    start, end = citation.span()
                    curr_segment = (
                        curr_segment[:start]
                        + f"[{target_citation_num}]"
                        + curr_segment[end:]
                    )

                    if target_citation_num not in cited_inds:
                        cited_inds.add(target_citation_num)
                        yield CitationInfo(
                            citation_num=target_citation_num,
                            document_id=context_llm_doc.document_id,
                        )

                    if link:
                        curr_segment = (
                            curr_segment[:start]
                            + f"[[{target_citation_num}]]({link})"
                            + curr_segment[end:]
                        )

                    last_citation_end = end
                    last_cited_num = target_citation_num

            if last_citation_end > 0:
                yield DanswerAnswerPiece(answer_piece=curr_segment[:last_citation_end])
                curr_segment = curr_segment[last_citation_end:]

    if curr_segment:
        yield DanswerAnswerPiece(answer_piece=curr_segment)


def build_citation_processor(
    context_docs: list[LlmDoc], search_order_docs: list[LlmDoc]
) -> StreamProcessor:
    def stream_processor(tokens: Iterator[str]) -> AnswerQuestionStreamReturn:
        yield from extract_citations_from_stream(
            tokens=tokens,
            context_docs=context_docs,
            doc_id_to_rank_map=map_document_id_order(search_order_docs),
        )

    return stream_processor
