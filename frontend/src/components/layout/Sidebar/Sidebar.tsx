import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import styles from  './Sidebar.module.scss';

const Sidebar: React.FC = () => {
  const location = useLocation();

  return (
    <nav className={styles['sidebar']}>
      <div className={styles['sidebar__brand']}>
        <div className={styles['sidebar__logo']}> 
          <span className="material-symbols-outlined">local_fire_department</span>
        </div>
        <div className={styles['sidebar__title']}>
          <h2 className={styles['sidebar__title-name']}>ГА</h2>
          <p className={styles['sidebar__title-sub']}>Газпром Автоматизация</p>
        </div>
      </div>

      <ul className={styles['sidebar__nav']}>
        <li className={styles['sidebar__item']}>
          <Link
            to="/"
            className={`${styles['sidebar__link']} ${location.pathname === '/' ? styles['sidebar__link--active'] : ''}`}
          >
            <span className="material-symbols-outlined" style={location.pathname === '/' ? { fontVariationSettings: "'FILL' 1" } : {}}>
              upload_file
            </span>
            <span>Загрузка</span>
          </Link>
        </li>
        <li className={styles['sidebar__item']}>
          <Link
            to="/passports"
            className={`${styles['sidebar__link']} ${location.pathname === '/passports' ? styles['sidebar__link--active'] : ''}`}
          >
            <span className="material-symbols-outlined" style={location.pathname === '/passports' ? { fontVariationSettings: "'FILL' 1" } : {}}>
              grid_view
            </span>
            <span>Паспорта</span>
          </Link>
        </li>
      </ul>

      <div className={styles['sidebar__footer']}>v1.0</div>
    </nav>
  );
};

export default Sidebar;
