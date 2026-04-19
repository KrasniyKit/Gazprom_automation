import React from 'react';
import styles from  './Header.module.scss';

type Props = { title?: string };

const Header: React.FC<Props> = ({ title }) => {
  return (
    <header className={styles['app-header']}>
      <div className={styles['app-header__left']}>
        <span className={styles['app-header__title']}>{title}</span>
      </div>
      <div className={styles['app-header__right']}>
        <button className={styles['app-header__icon']}><span className="material-symbols-outlined">notifications</span></button>
        <button className={styles['app-header__icon']}><span className="material-symbols-outlined">settings</span></button>
      </div>
    </header>
  );
};

export default Header;
