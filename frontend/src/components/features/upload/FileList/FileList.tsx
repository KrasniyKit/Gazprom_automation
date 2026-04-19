import React from 'react';
import FileItem from '@/components/features/upload/FileItem';
import styles from './FileList.module.scss';
import useStore from '@/store/useStore';

const FileList: React.FC = () => {
  const files = useStore((s) => s.files);

  return (
    <div className={styles['file-list']}>
      {!files.length && (
        <div className={styles['file-list__empty']}>Файлы еще не загружены.</div>
      )}
      {files.map((f) => (
        <FileItem
          key={f.id}
          name={f.name}
          size={f.size}
          status={f.status}
          passportId={f.passportId}
          errorMessage={f.errorMessage}
        />
      ))}
    </div>
  );
};

export default FileList;
