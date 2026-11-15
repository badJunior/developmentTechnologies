export class ApiError extends Error {
  constructor(status, problem) {
    super(problem.title ?? `HTTP ${status}`);
    this.status = status;
    this.type = problem.type;
    this.requestId = problem.request_id;
  }
  get userMessage() { return this.title ?? 'Что-то пошло не так'; }
}

export class ContractError extends Error {
  constructor(schemaName, violations) {
    super(`Response does not match schema ${schemaName}`);
    this.schemaName = schemaName;
  }
  get userMessage() { return 'Сервер прислал данные в неожиданном виде.'; }
}
