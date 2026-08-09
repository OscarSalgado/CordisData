"""Pydantic models for CORDIS and SEDIA data."""

from typing import Optional

from pydantic import BaseModel, Field


class Call(BaseModel):
    """EU research funding call."""

    reference: str = Field(..., description="Unique reference from API")
    topicId: str = Field(..., description="Topic identifier")
    title: str = Field(..., description="Call title")
    programme: str = Field(default="", description="EU programme name")
    programmeId: str = Field(default="", description="Programme identifier")
    cluster: str = Field(default="", description="Cluster within programme")
    callIdentifier: str = Field(default="", description="Call identifier")
    actionType: str = Field(default="", description="Type of action (RIA, IA, CSA, etc.)")
    deadline: str = Field(default="", description="Submission deadline (YYYY-MM-DD)")
    stage: str = Field(default="single", description="Submission stage (single or two-stage)")
    callStatus: str = Field(default="unknown", description="Status (open, closed, forthcoming)")
    budgetMin: Optional[int] = Field(default=None, description="Minimum budget in EUR")
    budgetMax: Optional[int] = Field(default=None, description="Maximum budget in EUR")
    expectedGrants: Optional[int] = Field(default=None, description="Expected number of grants")
    keywords: str = Field(default="", description="Keywords (comma-separated)")
    portalUrl: str = Field(default="", description="URL to official portal")

    model_config = {"extra": "allow"}


class Project(BaseModel):
    """Funded research project."""

    topicId: str = Field(..., description="Topic identifier")
    acronym: str = Field(default="", description="Project acronym")
    projectId: str = Field(..., description="Unique project identifier")
    euContributionAmount: Optional[int] = Field(default=None, description="EU contribution in EUR")
    overallBudget: Optional[int] = Field(default=None, description="Total project budget in EUR")
    status: str = Field(default="", description="Project status")
    startDate: str = Field(default="", description="Project start date (YYYY-MM-DD)")
    endDate: str = Field(default="", description="Project end date (YYYY-MM-DD)")
    legalEntityNames: list[str] = Field(default_factory=list, description="Participating entities")
    countries: list[str] = Field(default_factory=list, description="Participating countries")
    objective: Optional[str] = Field(default=None, description="Project objective (from CORDIS)")
    grantDoi: Optional[str] = Field(default=None, description="Grant DOI (from CORDIS)")
    lastEnrichedAt: str = Field(default="", description="Last CORDIS enrichment timestamp (YYYY-MM-DD)")

    model_config = {"extra": "allow"}
