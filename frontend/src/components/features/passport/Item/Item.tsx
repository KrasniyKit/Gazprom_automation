import React from 'react';
import sharedStyles from '../PassportTable/PassportTable.module.scss';
import Cell from '../Cell';
import useStore from '@/store/useStore';

type Row = {
  id: string;
  equipment_name: string;
  purpose: string;
  technical_specs: string;
  manufacturer: string;
  normative_docs: string;
  passport_number: string;
  issue_date: string;
  completeness: string;
  service_life: string;
  warranty: string;
  sourceFile?: string;
  uncertainFields?: Partial<Record<
    'equipment_name' | 'purpose' | 'technical_specs' |
    'manufacturer' | 'normative_docs' | 'passport_number' |
    'issue_date' | 'completeness' | 'service_life' | 'warranty',
    boolean
  >>;
};

type Props = {
  row: Row;
  idx: number;
  selected: boolean;
  toggleRow: (id: string) => void;
  onFieldChange: (id: string, field: keyof Row, value: string) => void;
};

const Item: React.FC<Props> = ({ row, idx, selected, toggleRow, onFieldChange }) => {
  const files = useStore((s) => s.files);
  const isWarnRow = Boolean(row.uncertainFields && Object.values(row.uncertainFields).some(Boolean));
  const rowClass = [sharedStyles['cards__row'], selected ? sharedStyles['cards__row--selected'] : '', isWarnRow ? sharedStyles['cards__row--warn'] : '']
    .filter(Boolean)
    .join(' ');
  const foundFile = files.find((f) => f.passportId === row.id || f.name === row.sourceFile);

  return (
    <tr id={`passport-${encodeURIComponent(row.id)}`} className={rowClass}>
      <td>
        <input type="checkbox" checked={selected} onChange={() => toggleRow(row.id)} />
      </td>
      <td>{idx + 1}</td>

      <Cell value={row.equipment_name} onChange={(v) => onFieldChange(row.id, 'equipment_name', v)} uncertain={!!row.uncertainFields?.equipment_name} />
      <Cell value={row.purpose} onChange={(v) => onFieldChange(row.id, 'purpose', v)} uncertain={!!row.uncertainFields?.purpose} />
      <Cell value={row.technical_specs} onChange={(v) => onFieldChange(row.id, 'technical_specs', v)} uncertain={!!row.uncertainFields?.technical_specs} />
      <Cell value={row.manufacturer} onChange={(v) => onFieldChange(row.id, 'manufacturer', v)} uncertain={!!row.uncertainFields?.manufacturer} />
      <Cell value={row.normative_docs} onChange={(v) => onFieldChange(row.id, 'normative_docs', v)} uncertain={!!row.uncertainFields?.normative_docs} />
      <Cell value={row.passport_number} onChange={(v) => onFieldChange(row.id, 'passport_number', v)} uncertain={!!row.uncertainFields?.passport_number} />
      <Cell value={row.issue_date} onChange={(v) => onFieldChange(row.id, 'issue_date', v)} uncertain={!!row.uncertainFields?.issue_date} />
      <Cell value={row.completeness} onChange={(v) => onFieldChange(row.id, 'completeness', v)} uncertain={!!row.uncertainFields?.completeness} />
      <Cell value={row.service_life} onChange={(v) => onFieldChange(row.id, 'service_life', v)} uncertain={!!row.uncertainFields?.service_life} />
      <Cell value={row.warranty} onChange={(v) => onFieldChange(row.id, 'warranty', v)} uncertain={!!row.uncertainFields?.warranty} />

      <td className={sharedStyles['cards__file']}>
        <div className={sharedStyles['cards__file-name']}>
          {foundFile ? (
            <a href={`#file-${foundFile.id}`}>{foundFile.name}</a>
          ) : (
            (row.sourceFile ?? '—')
          )}
        </div>
      </td>
    </tr>
  );
};

export default Item;
