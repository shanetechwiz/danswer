from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from danswer.db.models import StandardAnswer
from danswer.db.models import StandardAnswerCategory
from danswer.utils.logger import setup_logger

logger = setup_logger()


def check_category_validity(category_name: str) -> bool:
    """If a category name is too long, it should be used (it will cause an error in Postgres
    as the unique constraint can only apply to entries that are less than 2704 bytes).

    Additionally, extremely long categories are not really usable / useful."""
    if len(category_name) > 255:
        logger.error(
            f"Category with name '{category_name}' is too long, cannot be used"
        )
        return False

    return True


def insert_standard_answer_category(
    category_name: str, db_session: Session
) -> StandardAnswerCategory:
    if not check_category_validity(category_name):
        raise ValueError(f"Invalid category name: {category_name}")
    standard_answer_category = StandardAnswerCategory(name=category_name)
    db_session.add(standard_answer_category)
    db_session.commit()

    return standard_answer_category


def insert_standard_answer(
    keyword: str,
    answer: str,
    categories: list[int],
    db_session: Session,
) -> StandardAnswer:
    existing_categories = fetch_standard_answer_categories_by_ids(
        standard_answer_category_ids=categories,
        db_session=db_session,
    )
    if len(existing_categories) != len(categories):
        raise ValueError(f"Some or all categories with ids {categories} do not exist")

    standard_answer = StandardAnswer(
        keyword=keyword,
        answer=answer,
        categories=existing_categories,
    )
    db_session.add(standard_answer)
    db_session.commit()
    return standard_answer


def update_standard_answer(
    standard_answer_id: int,
    keyword: str,
    answer: str,
    categories: list[int],
    db_session: Session,
) -> StandardAnswer:
    standard_answer = db_session.scalar(
        select(StandardAnswer).where(StandardAnswer.id == standard_answer_id)
    )
    if standard_answer is None:
        raise ValueError(f"No standard answer with id {standard_answer_id}")

    existing_categories = fetch_standard_answer_categories_by_ids(
        standard_answer_category_ids=categories,
        db_session=db_session,
    )
    if len(existing_categories) != len(categories):
        raise ValueError(f"Some or all categories with ids {categories} do not exist")

    standard_answer.keyword = keyword
    standard_answer.answer = answer
    standard_answer.categories = existing_categories

    db_session.commit()

    return standard_answer


def remove_standard_answer(
    standard_answer_id: int,
    db_session: Session,
) -> None:
    standard_answer = db_session.scalar(
        select(StandardAnswer).where(StandardAnswer.id == standard_answer_id)
    )
    if standard_answer is None:
        raise ValueError(f"No standard answer with id {standard_answer_id}")

    db_session.delete(standard_answer)
    db_session.commit()


def update_standard_answer_category(
    standard_answer_category_id: int,
    category_name: str,
    db_session: Session,
) -> StandardAnswerCategory:
    standard_answer_category = db_session.scalar(
        select(StandardAnswerCategory).where(
            StandardAnswerCategory.id == standard_answer_category_id
        )
    )
    if standard_answer_category is None:
        raise ValueError(
            f"No standard answer category with id {standard_answer_category_id}"
        )

    if not check_category_validity(category_name):
        raise ValueError(f"Invalid category name: {category_name}")

    standard_answer_category.name = category_name

    db_session.commit()

    return standard_answer_category


def fetch_standard_answer_category(
    standard_answer_category_id: int,
    db_session: Session,
) -> StandardAnswerCategory | None:
    return db_session.scalar(
        select(StandardAnswerCategory).where(
            StandardAnswerCategory.id == standard_answer_category_id
        )
    )


def fetch_standard_answer_categories_by_ids(
    standard_answer_category_ids: list[int],
    db_session: Session,
) -> list[StandardAnswerCategory]:
    return db_session.scalars(
        select(StandardAnswerCategory).where(
            StandardAnswerCategory.id.in_(standard_answer_category_ids)
        )
    ).all()


def fetch_standard_answer_categories(
    db_session: Session,
) -> Sequence[StandardAnswerCategory]:
    return db_session.scalars(select(StandardAnswerCategory)).all()


def fetch_standard_answer(
    standard_answer_id: int,
    db_session: Session,
) -> StandardAnswer | None:
    return db_session.scalar(
        select(StandardAnswer).where(StandardAnswer.id == standard_answer_id)
    )


def fetch_standard_answers(db_session: Session) -> Sequence[StandardAnswer]:
    return db_session.scalars(select(StandardAnswer)).all()
