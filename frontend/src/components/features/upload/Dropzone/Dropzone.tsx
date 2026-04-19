import React from 'react';
import styles from './Dropzone.module.scss';

const Dropzone: React.FC = () => {
  return (
    <div className={styles.dropzone} role="button" tabIndex={0}>
      <span className={`material-symbols-outlined ${styles['dropzone__icon']}`}>upload</span>
      <p className={styles['dropzone__text']}>Перетащите PDF файлы сюда</p>
      <p className={styles['dropzone__or']}>или</p>
      <button className={styles['dropzone__btn']}>Выбрать файлы</button>
    </div>
  );
};

export default Dropzone;
