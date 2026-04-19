import React from 'react';
import sharedStyles from '../PassportTable/PassportTable.module.scss';
import Cell from '../Cell';

type Row = {
  id: string;
  name: string;
  code: string;
  factoryNumber: string;
  manufacturer: string;
  date: string;
  warranty: string;
  sourceFile?: string;
  uncertainFields?: Partial<Record<'name' | 'code' | 'factoryNumber' | 'manufacturer' | 'date' | 'warranty', boolean>>;
};

type Props = {
  row: Row;
  idx: number;
  selected: boolean;
  toggleRow: (id: string) => void;
  onFieldChange: (id: string, field: keyof Row, value: string) => void;
};

const Item: React.FC<Props> = ({ row, idx, selected, toggleRow, onFieldChange }) => {
  const isWarnRow = Boolean(row.uncertainFields && Object.values(row.uncertainFields).some(Boolean));
  const rowClass = [sharedStyles['cards__row'], selected ? sharedStyles['cards__row--selected'] : '', isWarnRow ? sharedStyles['cards__row--warn'] : '']
    .filter(Boolean)
    .join(' ');

  return (
    <tr id={`passport-${encodeURIComponent(row.id)}`} className={rowClass}>
      <td>
        <input type="checkbox" checked={selected} onChange={() => toggleRow(row.id)} />
      </td>
      <td>{idx + 1}</td>

      <Cell value={row.name} onChange={(v) => onFieldChange(row.id, 'name', v)} uncertain={!!row.uncertainFields?.name} />
      <Cell value={row.code} onChange={(v) => onFieldChange(row.id, 'code', v)} uncertain={!!row.uncertainFields?.code} />
      <Cell value={row.factoryNumber} onChange={(v) => onFieldChange(row.id, 'factoryNumber', v)} uncertain={!!row.uncertainFields?.factoryNumber} />
      <Cell value={row.manufacturer} onChange={(v) => onFieldChange(row.id, 'manufacturer', v)} uncertain={!!row.uncertainFields?.manufacturer} />
      <Cell value={row.date} onChange={(v) => onFieldChange(row.id, 'date', v)} uncertain={!!row.uncertainFields?.date} />
      <Cell value={row.warranty} onChange={(v) => onFieldChange(row.id, 'warranty', v)} uncertain={!!row.uncertainFields?.warranty} />

      <td className={sharedStyles['cards__file']}>
        <div className={sharedStyles['cards__file-name']}>{row.sourceFile ?? '—'}</div>
      </td>
    </tr>
  );
};

export default Item;
