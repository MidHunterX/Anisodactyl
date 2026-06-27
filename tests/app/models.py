from typing import List, Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(primary_key=True)


class ParentModel(Base):
    __tablename__ = "test_parent_model"
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[Optional[str]] = mapped_column()
    # 1:1 central relationship
    model: Mapped[Optional["Model"]] = relationship("Model", back_populates="parent")


class Model(Base):
    __tablename__ = "test_model"
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[Optional[str]] = mapped_column()
    # 1:1 child relationships
    child: Mapped[Optional["ChildModel"]] = relationship(
        "ChildModel", back_populates="parent"
    )
    child2: Mapped[Optional["ChildModel2"]] = relationship(
        "ChildModel2", back_populates="parent"
    )
    # 1:N child relationship (Collection)
    contacts: Mapped[List["ContactModel"]] = relationship(
        "ContactModel", back_populates="parent"
    )
    # FK: parent
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("test_parent_model.id"))
    parent: Mapped[Optional["ParentModel"]] = relationship(
        "ParentModel", back_populates="model"
    )


class ChildModel(Base):
    __tablename__ = "test_child_model"
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[Optional[str]] = mapped_column()
    # FK: tarsometatarsus
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("test_model.id"))
    parent: Mapped[Optional["Model"]] = relationship("Model", back_populates="child")


class ChildModel2(Base):
    __tablename__ = "test_child_model2"
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[Optional[str]] = mapped_column()
    # FK: tarsometatarsus
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("test_model.id"))
    parent: Mapped[Optional["Model"]] = relationship("Model", back_populates="child2")


class ContactModel(Base):
    __tablename__ = "test_contact_model"
    name: Mapped[str] = mapped_column(nullable=False)
    value: Mapped[str] = mapped_column(nullable=False)
    # FK: tarsometatarsus
    parent_id: Mapped[int] = mapped_column(ForeignKey("test_model.id"))
    parent: Mapped["Model"] = relationship("Model", back_populates="contacts")
