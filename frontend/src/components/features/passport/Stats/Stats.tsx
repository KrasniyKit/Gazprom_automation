import React from 'react';
import styles from './Stats.module.scss';

const Stats: React.FC = () => {
  return (
    <div className={styles['cards__stats']}>
      <div className={styles['cards__stat']}> <div className={styles['cards__stat-label']}>Всего паспортов</div> <div className={styles['cards__stat-value']}>17</div> </div>
      <div className={styles['cards__stat']}> <div className={styles['cards__stat-label']}>Обработано</div> <div className={`${styles['cards__stat-value']} ${styles['cards__stat-value--processed']}`}>15</div> </div>
      <div className={`${styles['cards__stat']} ${styles['cards__stat--warn']}`}> <div className={styles['cards__stat-label']}>Требуют проверки</div> <div className={styles['cards__stat-value']}>3</div> </div>
    </div>
  );
};

export default Stats;
