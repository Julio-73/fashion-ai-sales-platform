from app.modules.companies.repository import CompanyRepository


class CompanyService:
    def __init__(self, repository: CompanyRepository) -> None:
        self._repository = repository

