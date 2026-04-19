import React from 'react';
import Header from '@/components/layout/Header';
import Dropzone from '@/components/features/upload/Dropzone';
import FileList from '@/components/features/upload/FileList';
import styles from './PassportUpload.module.scss';

const PassportUpload: React.FC = () => {
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
