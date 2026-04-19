import React, { useEffect } from 'react';
import Header from '@/components/layout/Header';
import Dropzone from '@/components/features/upload/Dropzone';
import FileList from '@/components/features/upload/FileList';
import styles from './PassportUpload.module.scss';

const PassportUpload: React.FC = () => {
  useEffect(() => {
    const prevBodyOverflow = document.body.style.overflow;
    const prevHtmlOverflow = document.documentElement.style.overflow;
    document.body.style.overflow = 'hidden';
    document.documentElement.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = prevBodyOverflow;
      document.documentElement.style.overflow = prevHtmlOverflow;
    };
  }, []);

  return (
    <main className={styles['page--upload']}>
      <Header title="Загрузка паспортов оборудования" />

      <div className={styles['page__content']}>
        <div className={styles['passport-upload']}>
          <div className={styles['passport-upload__hero']}>
            <h1 className={styles['passport-upload__title']}>Загрузка паспортов</h1>
            <p className={styles['passport-upload__subtitle']}>Поддерживаются PDF файлы до 50 МБ</p>
          </div>

          <Dropzone />

          <FileList />
        </div>
      </div>
    </main>
  );
};

export default PassportUpload;
