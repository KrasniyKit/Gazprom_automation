import React, { useState } from 'react';
import styles from './PassportTable.module.scss';
import Item from '../Item';
import useStore from '@/store/useStore';

export type PassportProps = {
  selectAll: boolean;
  selectedRows: boolean[];
  toggleAll: () => void;
  toggleRow: (i: number) => void;
  openExport: () => void;
};

const PassportTable: React.FC<PassportProps> = ({ selectAll, selectedRows, toggleAll, toggleRow, openExport }) => {
  type Row = {
    name: string;
    code: string;
    factoryNumber: string;
    manufacturer: string;
    date: string;
    warranty: string;
    sourceFile?: string;
    // optional flags from OCR indicating uncertain fields
    uncertainFields?: Partial<Record<'name' | 'code' | 'factoryNumber' | 'manufacturer' | 'date' | 'warranty', boolean>>;
  };

  const initialRows: Row[] = [
    { name: 'Название 1', code: 'Код-1', factoryNumber: '10245-A', manufacturer: 'Производитель', date: '2023-01-01', warranty: '24 мес.', sourceFile: 'passport_eq_001.pdf' },
    { name: 'Название 2', code: 'Код-2', factoryNumber: '', manufacturer: 'Производитель', date: '2023-01-01', warranty: '24 мес.', uncertainFields: { factoryNumber: true }, sourceFile: 'technical_spec_v2.pdf' },
    { name: 'Название 3', code: 'Код-3', factoryNumber: '33910', manufacturer: 'Производитель', date: '2023-01-01', warranty: '24 мес.', sourceFile: 'manual_pump_z400.pdf' },
    { name: 'Название 4', code: 'Код-4', factoryNumber: '10245-A', manufacturer: 'Производитель', date: '2023-01-01', warranty: '24 мес.', sourceFile: 'corrupted_file.pdf' },
  ];

  const [rows, setRows] = useState<Row[]>(initialRows);

  const handleChange = (index: number, field: keyof Row, value: string) => {
    setRows(prev => {
      const next = [...prev];
      next[index] = { ...next[index], [field]: value };
      return next;
    });
  };

  return (
    <div className={styles['cards__table-wrap']}>
      <table className={styles['cards__table']}>
        <thead>
          <tr>
            <th><label className={styles['cards__select-all']}><input type="checkbox" checked={selectAll} onChange={toggleAll} /><span>Выбрать все</span></label></th>
            <th>№</th>
            <th>Наименование</th>
            <th>Обозначение ПС</th>
            <th>Заводской номер</th>
            <th>Изготовитель</th>
            <th>Дата</th>
            <th>Гарантия</th>
            <th>Файл</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, idx) => (
            <Item
              key={idx}
              row={row}
              idx={idx}
              selected={!!selectedRows[idx]}
              toggleRow={toggleRow}
              onFieldChange={handleChange}
            />
          ))}
        </tbody>
      </table>

    </div>
  );
};

export default PassportTable;
