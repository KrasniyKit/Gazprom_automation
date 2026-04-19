import React from 'react';
import sharedStyles from '../PassportTable/PassportTable.module.scss';
import styles from './Cell.module.scss';

type Props = {
  value: string;
  onChange: (v: string) => void;
  uncertain?: boolean;
  inputType?: string;
};

const Cell: React.FC<Props> = ({ value, onChange, uncertain = false, inputType = 'text' }) => {
  return (
    <td className={uncertain ? sharedStyles['cards__cell--warn'] : undefined}>
      <div>
        {uncertain && (
          <div className={sharedStyles['cards__uncertain-badge']}>
            <span className="material-symbols-outlined">warning</span>
          </div>
        )}
        <input
          className={sharedStyles['cards__input']}
          type={inputType}
          value={value}
          onChange={(e) => onChange(e.target.value)}
        />
      </div>
    </td>
  );
};

export default Cell;
