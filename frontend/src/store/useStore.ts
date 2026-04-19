import { create } from 'zustand';

export type FileRecord = { name: string; size: string; status: 'done'|'processing'|'pending'|'error' };
export type PassportRow = {
  name: string;
  code: string;
  factoryNumber: string;
  manufacturer: string;
  date: string;
  warranty: string;
  sourceFile?: string;
  uncertainFields?: Partial<Record<'name' | 'code' | 'factoryNumber' | 'manufacturer' | 'date' | 'warranty', boolean>>;
};

type Store = {
  files: FileRecord[];
  passports: PassportRow[];
  selectedRows: boolean[];
  selectAll: boolean;

  // actions
  toggleRow: (i: number) => void;
  toggleAll: () => void;
  updateRowField: (index: number, field: keyof PassportRow, value: string) => void;
  addFile: (file: FileRecord) => void;
  updateFileStatus: (name: string, status: FileRecord['status']) => void;
};

const initialFiles: FileRecord[] = [
  { name: 'passport_eq_001.pdf', size: '2.4 MB', status: 'done' },
  { name: 'technical_spec_v2.pdf', size: '15.1 MB', status: 'processing' },
  { name: 'manual_pump_z400.pdf', size: '8.7 MB', status: 'pending' },
  { name: 'corrupted_file.pdf', size: '0.1 MB', status: 'error' },
];

const initialPassports: PassportRow[] = [
  { name: 'Название 1', code: 'Код-1', factoryNumber: '10245-A', manufacturer: 'Производитель', date: '2023-01-01', warranty: '24 мес.', sourceFile: 'passport_eq_001.pdf' },
  { name: 'Название 2', code: 'Код-2', factoryNumber: '', manufacturer: 'Производитель', date: '2023-01-01', warranty: '24 мес.', uncertainFields: { factoryNumber: true }, sourceFile: 'technical_spec_v2.pdf' },
  { name: 'Название 3', code: 'Код-3', factoryNumber: '33910', manufacturer: 'Производитель', date: '2023-01-01', warranty: '24 мес.', sourceFile: 'manual_pump_z400.pdf' },
  { name: 'Название 4', code: 'Код-4', factoryNumber: '10245-A', manufacturer: 'Производитель', date: '2023-01-01', warranty: '24 мес.', sourceFile: 'corrupted_file.pdf' },
];

const useStore = create<Store>((set, get) => ({
  files: initialFiles,
  passports: initialPassports,
  selectedRows: initialPassports.map((_, i) => false),
  selectAll: false,

  toggleRow: (i) => set(state => {
    const next = [...state.selectedRows];
    next[i] = !next[i];
    return { selectedRows: next, selectAll: next.every(Boolean) };
  }),

  toggleAll: () => set(state => {
    const newVal = !state.selectAll;
    return { selectAll: newVal, selectedRows: state.selectedRows.map(() => newVal) };
  }),

  updateRowField: (index, field, value) => set(state => {
    const next = [...state.passports];
    // @ts-ignore
    next[index] = { ...next[index], [field]: value };
    return { passports: next };
  }),

  addFile: (file) => set(state => ({ files: [...state.files, file] })),

  updateFileStatus: (name, status) => set(state => ({ files: state.files.map(f => f.name === name ? { ...f, status } : f) })),
}));

export default useStore;
