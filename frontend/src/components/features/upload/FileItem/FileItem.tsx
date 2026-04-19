import React from 'react';
import { Link } from 'react-router-dom';
import styles from './FileItem.module.scss';

export type FileItemProps = { name: string; size: string; status: 'done'|'processing'|'pending'|'error' };

const slugify = (s: string) => encodeURIComponent(s.replace(/\.[^/.]+$/, '').replace(/\s+/g, '-').toLowerCase());

const FileItem: React.FC<FileItemProps> = ({ name, size, status }) => {
  const outerClass = `${styles['file-item']} ${styles[`file-item--${status}`]}`;

  return (
    <div className={outerClass}>
      <span className={`material-symbols-outlined ${styles['file-item__icon']}`}>description</span>
      <div className={styles['file-item__meta']}>
        <div className={styles['file-item__name']}>{name}</div>
        <div className={styles['file-item__size']}>{size}</div>
      </div>
      <div className={styles['file-item__status']}>{status === 'done' ? 'Готово' : status === 'processing' ? 'Обработка...' : status === 'pending' ? 'Ожидает' : 'Ошибка'}</div>
      {status === 'done' && (
        <Link to={`/passports#passport-${slugify(name)}`} className={styles['file-item__view']} title="Открыть паспорт">
          <span className="material-symbols-outlined">visibility</span>
        </Link>
      )}

      {status === 'processing' && (
        <div className={styles['file-item__processing']} title="В обработке">
          <span className="material-symbols-outlined">autorenew</span>
        </div>
      )}
    </div>
  );
};

export default FileItem;
