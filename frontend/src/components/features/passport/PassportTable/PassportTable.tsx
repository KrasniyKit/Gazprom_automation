import React from 'react';
import styles from './PassportTable.module.scss';
import Item from '../Item';
import useStore from '@/store/useStore';

const PassportTable: React.FC = () => {
  const selectAll = useStore((s) => s.selectAll);
  const selectedIds = useStore((s) => s.selectedIds);
  const toggleAll = useStore((s) => s.toggleAll);
  const toggleRow = useStore((s) => s.toggleRow);
  const passports = useStore((s) => s.passports);
  const updateRowField = useStore((s) => s.updateRowField);

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
          {passports.map((row, idx) => (
            <Item
              key={row.id}
              row={row}
              idx={idx}
              selected={selectedIds.includes(row.id)}
              toggleRow={toggleRow}
              onFieldChange={updateRowField}
            />
          ))}
        </tbody>
      </table>

    </div>
  );
};

export default PassportTable;
