import React from 'react';
import { Link } from 'react-router-dom';
import styles from './FileItem.module.scss';
import type { FileRecord } from '@/store/useStore';

export type FileItemProps = Pick<FileRecord, 'name' | 'size' | 'status' | 'passportId' | 'errorMessage'>;

const FileItem: React.FC<FileItemProps> = ({ name, size, status, passportId, errorMessage }) => {
  const outerClass = `${styles['file-item']} ${styles[`file-item--${status}`]}`;
  const statusText =
    status === 'done'
      ? 'Готово'
      : status === 'processing'
        ? 'Обработка...'
        : status === 'pending'
          ? 'Ожидает'
          : 'Ошибка';

  return (
    <div className={outerClass}>
      <span className={`material-symbols-outlined ${styles['file-item__icon']}`}>description</span>
      <div className={styles['file-item__meta']}>
        <div className={styles['file-item__name']}>{name}</div>
        <div className={styles['file-item__size']}>{size}</div>
      </div>
      <div className={styles['file-item__status']} title={errorMessage ?? undefined}>{statusText}</div>
      {status === 'done' && passportId && (
        <Link to={`/passports#passport-${encodeURIComponent(passportId)}`} className={styles['file-item__view']} title="Открыть паспорт">
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
