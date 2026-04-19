import React from 'react';
import styles from './Stats.module.scss';
import useStore from '@/store/useStore';

const Stats: React.FC = () => {
  const passports = useStore(s => s.passports);
  const total = passports.length;
  const fieldsToCheck = passports.reduce((acc, p) => {
    if (!p.uncertainFields) return acc;
    return acc + Object.values(p.uncertainFields).filter(Boolean).length;
  }, 0);

  return (
    <div className={styles['cards__stats']}>
      <div className={styles['cards__stat']}> <div className={styles['cards__stat-label']}>Всего паспортов</div> <div className={styles['cards__stat-value']}>{total}</div> </div>
      <div className={`${styles['cards__stat']} ${styles['cards__stat--warn']}`}> <div className={styles['cards__stat-label']}>Требуют проверки</div> <div className={styles['cards__stat-value']}>{fieldsToCheck}</div> </div>
    </div>
  );
};

export default Stats;
