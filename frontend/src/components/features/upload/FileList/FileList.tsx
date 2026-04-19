import React from 'react';
import FileItem from '@/components/features/upload/FileItem';
import styles from './FileList.module.scss';
import useStore from '@/store/useStore';

const FileList: React.FC = () => {
  const files = useStore(s => s.files);

  return (
    <div className={styles['file-list']}>
      {files.map((f) => (
        <FileItem key={f.name} name={f.name} size={f.size} status={f.status as any} />
      ))}
    </div>
  );
};

export default FileList;
