from pydantic import BaseModel


class FieldMapping(BaseModel):
    identifier: str
    columnName: str


class EntityMapping(BaseModel):
    entityType: str
    fieldMappings: list[FieldMapping]


class Tag(BaseModel):
    Id: str
    version: str


class Detection(BaseModel):
    id: str
    name: str
    description: str
    severity: str
    requiredDataConnectors: list[str]
    queryFrequency: str
    queryPeriod: str
    triggerOperator: str
    triggerThreshold: int
    tactics: list[str]
    relevantTechniques: list[str]
    query: str
    tags: list[Tag]
    version: str
    kind: str
    metadata: dict

    # @validator('relevantTechniques')
    # def must_be_technique_id(cls, v):
    #     if ' ' not in v:
    #         raise ValueError('must contain a space')
    #     return v.title()
