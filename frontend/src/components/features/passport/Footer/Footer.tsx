import React from 'react';
import styles from './Footer.module.scss';

export type FooterProps = {
  selectedCount?: number;
  onDelete?: () => void;
  onReset?: () => void;
  onSave?: () => void;
  className?: string;
};

const Footer: React.FC<FooterProps> = ({ selectedCount = 0, onDelete, onReset, onSave, className }) => {
  const deleteDisabled = selectedCount === 0;

  return (
    <footer className={`${styles.footer} ${className || ''}`.trim()}>
      <div className={styles.left}>
        Изменено: <span className={styles.count}>{selectedCount} {selectedCount === 1 ? 'поле' : 'поля'}</span>
      </div>

      <div className={styles.actions}>
        <button
          onClick={onDelete}
          disabled={deleteDisabled}
          className={`${styles.btn} ${styles['btn--delete']} ${deleteDisabled ? styles['is-disabled'] : ''}`.trim()}
        >
          <span className="material-symbols-outlined">delete</span>
          Удалить выбранные
        </button>

        <button onClick={onReset} className={`${styles.btn} ${styles['btn--muted']}`}>
          Сбросить
        </button>

        <button onClick={onSave} className={`${styles.btn} ${styles['btn--save']}`}>
          <span className="material-symbols-outlined">save</span>
          Сохранить в Excel
        </button>
      </div>
    </footer>
  );
};

export default Footer;
