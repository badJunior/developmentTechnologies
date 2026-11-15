import Ajv2020 from 'ajv/dist/2020.js';
import addFormats from 'ajv-formats';
import { ContractError } from './errors.js';
import { schemas } from './schemas.js';

const ajv = new Ajv2020({ allErrors: true, strict: false });
addFormats(ajv);

export function validateResponse(schemaName, payload) {
  const schema = schemas[schemaName];
  if (!schema) throw new Error(`Схема ${schemaName} отсутствует`);
  const validate = ajv.compile({ ...schema, definitions: schemas.definitions });
  if (!validate(payload)) throw new ContractError(schemaName, validate.errors);
  return payload;
}
