import { readFileSync, writeFileSync } from 'node:fs';
import * as yaml from 'js-yaml';

const spec = yaml.load(readFileSync('../docs/api/openapi.yaml', 'utf8'));
const schemas = JSON.parse(
  JSON.stringify(spec.components.schemas).replaceAll(
    '#/components/schemas/', '#/definitions/',
  ),
);

const EXTENSIBLE_ENUMS = ['SeatKind', 'BookingStatus'];
for (const name of EXTENSIBLE_ENUMS) {
  if (schemas[name]) delete schemas[name].enum;
}

writeFileSync(
  'src/api/schemas.js',
  `// ПОРОЖДЕННЫЙ ФАЙЛ. Не править руками.\n` +
  `export const schemas = ${JSON.stringify({ definitions: schemas, ...schemas }, null, 2)};\n`,
);
