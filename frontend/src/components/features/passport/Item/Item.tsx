import React from 'react';
import sharedStyles from '../PassportTable/PassportTable.module.scss';
import Cell from '../Cell';
import styles from './Item.module.scss';

type Row = {
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
  toggleRow: (i: number) => void;
  onFieldChange: (index: number, field: keyof Row, value: string) => void;
};

const Item: React.FC<Props> = ({ row, idx, selected, toggleRow, onFieldChange }) => {
  const isWarnRow = Boolean(row.uncertainFields && Object.values(row.uncertainFields).some(Boolean));
  const rowClass = [sharedStyles['cards__row'], selected ? sharedStyles['cards__row--selected'] : '', isWarnRow ? sharedStyles['cards__row--warn'] : '']
    .filter(Boolean)
    .join(' ');

  const slugify = (s: string) => encodeURIComponent(s.replace(/\s+/g, '-').toLowerCase());

  return (
    <tr id={`passport-${slugify(row.name)}`} className={rowClass}>
      <td>
        <input type="checkbox" checked={selected} onChange={() => toggleRow(idx)} />
      </td>
      <td>{idx + 1}</td>

      <Cell value={row.name} onChange={(v) => onFieldChange(idx, 'name', v)} uncertain={!!row.uncertainFields?.name} />
      <Cell value={row.code} onChange={(v) => onFieldChange(idx, 'code', v)} uncertain={!!row.uncertainFields?.code} />
      <Cell value={row.factoryNumber} onChange={(v) => onFieldChange(idx, 'factoryNumber', v)} uncertain={!!row.uncertainFields?.factoryNumber} />
      <Cell value={row.manufacturer} onChange={(v) => onFieldChange(idx, 'manufacturer', v)} uncertain={!!row.uncertainFields?.manufacturer} />
      <Cell value={row.date} onChange={(v) => onFieldChange(idx, 'date', v)} uncertain={!!row.uncertainFields?.date} />
      <Cell value={row.warranty} onChange={(v) => onFieldChange(idx, 'warranty', v)} uncertain={!!row.uncertainFields?.warranty} />

      <td className={sharedStyles['cards__file']}>
        <div className={sharedStyles['cards__file-name']}>{row.sourceFile ?? '—'}</div>
      </td>
    </tr>
  );
};

export default Item;
