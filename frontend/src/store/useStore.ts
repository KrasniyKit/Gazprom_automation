import axios from 'axios';
import { create } from 'zustand';
import * as XLSX from 'xlsx';

export type FileStatus = 'done' | 'processing' | 'pending' | 'error';
export type FileRecord = {
  id: string;
  name: string;
  size: string;
  status: FileStatus;
  passportId?: string;
  errorMessage?: string;
};

export type PassportRow = {
  id: string;
  equipment_name: string;
  purpose: string;
  technical_specs: string;
  manufacturer: string;
  normative_docs: string;
  passport_number: string;
  issue_date: string;
  completeness: string;
  service_life: string;
  warranty: string;
  sourceFile?: string;
  uncertainFields?: Partial<Record<
    'equipment_name' | 'purpose' | 'technical_specs' |
    'manufacturer' | 'normative_docs' | 'passport_number' |
    'issue_date' | 'completeness' | 'service_life' | 'warranty',
    boolean
  >>;
};

type Store = {
  files: FileRecord[];
  passports: PassportRow[];
  originalPassports: Record<string, PassportRow>;
  selectedIds: string[];
  selectAll: boolean;
  isUploading: boolean;
  uploadError: string | null;
  isExporting: boolean;
  exportError: string | null;

  toggleRow: (id: string) => void;
  toggleAll: () => void;
  updateRowField: (id: string, field: keyof PassportRow, value: string) => void;
  addFile: (file: FileRecord) => void;
  updateFileStatus: (name: string, status: FileRecord['status']) => void;
  deleteSelected: () => void;
  resetSelected: () => void;
  clearUploadError: () => void;
  clearExportError: () => void;
  uploadFiles: (files: File[]) => Promise<void>;
  exportSelectedToExcel: (deleteAfterExport: boolean) => Promise<void>;
};

const initialFiles: FileRecord[] = [];
const initialPassports: PassportRow[] = [];

const makeId = () => {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) return crypto.randomUUID();
  return `id-${Date.now()}-${Math.random().toString(16).slice(2)}`;
};

const toFileSize = (bytes: number) => {
  if (bytes < 1024) return `${bytes} B`;
  const units = ['KB', 'MB', 'GB'];
  let size = bytes / 1024;
  let unitIndex = 0;
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex += 1;
  }
  return `${size.toFixed(1)} ${units[unitIndex]}`;
};

const normalizeUncertainFields = (value: unknown): PassportRow['uncertainFields'] => {
  const allowed = [
    'equipment_name',
    'purpose',
    'technical_specs',
    'manufacturer',
    'normative_docs',
    'passport_number',
    'issue_date',
    'completeness',
    'service_life',
    'warranty',
  ] as const;
  const result: PassportRow['uncertainFields'] = {};
  if (Array.isArray(value)) {
    value.forEach((item) => {
      if (typeof item === 'string' && (allowed as readonly string[]).includes(item)) {
        result[item as keyof typeof result] = true;
      }
    });
  } else if (value && typeof value === 'object') {
    allowed.forEach((key) => {
      const boolValue = (value as Record<string, unknown>)[key];
      if (typeof boolValue === 'boolean') result[key] = boolValue;
    });
  } else {
    return undefined;
  }
  return Object.keys(result).length ? result : undefined;
};

const mapPassportResponse = (rawData: unknown, file: File): PassportRow => {
  const payload =
    Array.isArray(rawData) ? rawData[0] :
    (rawData as { card?: unknown; passport?: unknown })?.card ??
    (rawData as { card?: unknown; passport?: unknown })?.passport ??
    rawData;

  const obj = (payload && typeof payload === 'object') ? (payload as Record<string, unknown>) : {};
  const id = String(obj.id ?? makeId());
  const source = (obj.source && typeof obj.source === 'object') ? (obj.source as Record<string, unknown>) : undefined;
  const sourceFile = String(source?.file_name ?? obj.sourceFile ?? obj.fileName ?? file.name);
  const issueDateValue = obj.issue_date ?? obj.issueDate ?? '';

  const parseDateToISO = (val: unknown): string => {
    if (!val && val !== 0) return '';
    if (val instanceof Date && !isNaN(val.getTime())) return val.toISOString().slice(0, 10);
    if (typeof val === 'number') {
      const d = new Date(val);
      return isNaN(d.getTime()) ? '' : d.toISOString().slice(0, 10);
    }
    if (typeof val === 'string') {
      const s = val.trim();
      if (!s) return '';
      // If already in YYYY-MM-DD or starts with ISO date, take first 10 chars
      const isoLike = /^\d{4}-\d{2}-\d{2}/;
      const match = s.match(isoLike);
      if (match) return match[0];
      const parsed = Date.parse(s);
      if (!isNaN(parsed)) return new Date(parsed).toISOString().slice(0, 10);
      return s; // fallback to original string
    }
    return '';
  };

  const issueDateString = parseDateToISO(issueDateValue);

  return {
    id,
    equipment_name: String(obj.equipment_name ?? obj.equipmentName ?? obj.name ?? file.name.replace(/\.[^/.]+$/, '')),
    purpose: String(obj.purpose ?? ''),
    technical_specs: String(obj.technical_specs ?? obj.technicalSpecs ?? ''),
    manufacturer: String(obj.manufacturer ?? obj.vendor ?? ''),
    normative_docs: String(obj.normative_docs ?? obj.normativeDocs ?? ''),
    passport_number: String(obj.passport_number ?? obj.passportNumber ?? ''),
    issue_date: issueDateString,
    completeness: String(obj.completeness ?? ''),
    service_life: String(obj.service_life ?? obj.serviceLife ?? ''),
    warranty: String(obj.warranty ?? obj.warrantyPeriod ?? ''),
    sourceFile,
    uncertainFields: normalizeUncertainFields(obj.uncertain_fields ?? obj.uncertainFields),
  };
};

const useStore = create<Store>((set, get) => {
  const originalMap: Record<string, PassportRow> = initialPassports.reduce((acc, p) => {
    acc[p.id] = { ...p };
    return acc;
  }, {} as Record<string, PassportRow>);

  return {
    files: initialFiles,
    passports: initialPassports,
    originalPassports: originalMap,
    selectedIds: [],
    selectAll: false,
    isUploading: false,
    uploadError: null,
    isExporting: false,
    exportError: null,

    toggleRow: (id) => set((state) => {
      const nextSet = new Set(state.selectedIds);
      if (nextSet.has(id)) nextSet.delete(id);
      else nextSet.add(id);
      const next = Array.from(nextSet);
      return { selectedIds: next, selectAll: next.length > 0 && next.length === state.passports.length };
    }),

    toggleAll: () => set((state) => {
      const newVal = !state.selectAll;
      return { selectAll: newVal, selectedIds: newVal ? state.passports.map((p) => p.id) : [] };
    }),

    updateRowField: (id, field, value) => set((state) => ({
      passports: state.passports.map((p) => (p.id === id ? { ...p, [field]: value } : p)),
    })),

    addFile: (file) => set((state) => ({ files: [file, ...state.files] })),

    updateFileStatus: (name, status) => set((state) => ({
      files: state.files.map((f) => (f.name === name ? { ...f, status } : f)),
    })),

    deleteSelected: () => set((state) => {
      const selectedSet = new Set(state.selectedIds);
      const nextPassports = state.passports.filter((p) => !selectedSet.has(p.id));
      const nextOriginal: Record<string, PassportRow> = {};
      nextPassports.forEach((p) => {
        nextOriginal[p.id] = state.originalPassports[p.id] ?? { ...p };
      });
      return {
        passports: nextPassports,
        originalPassports: nextOriginal,
        selectedIds: [],
        selectAll: false,
      };
    }),

    resetSelected: () => set((state) => {
      const selectedSet = new Set(state.selectedIds);
      return {
        passports: state.passports.map((p) => (selectedSet.has(p.id) ? (state.originalPassports[p.id] ?? p) : p)),
      };
    }),

    clearUploadError: () => set({ uploadError: null }),
    clearExportError: () => set({ exportError: null }),

    uploadFiles: async (files) => {
      if (!files.length) return;

      const apiBase = (import.meta.env.VITE_API_URL ?? '').replace(/\/$/, '');
      const endpoint = import.meta.env.VITE_UPLOAD_ENDPOINT ?? '/api/passports/upload';
      const uploadUrl = endpoint.startsWith('http') ? endpoint : `${apiBase}${endpoint}`;

      set({ isUploading: true, uploadError: null });

      for (const file of files) {
        const fileId = makeId();
        set((state) => ({
          files: [
            {
              id: fileId,
              name: file.name,
              size: toFileSize(file.size),
              status: 'processing',
            },
            ...state.files,
          ],
        }));

        try {
          const formData = new FormData();
          formData.append('file', file);
          const response = await axios.post(uploadUrl, formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
          });

          const passport = mapPassportResponse(response.data, file);
          set((state) => ({
            files: state.files.map((f) => (f.id === fileId ? { ...f, status: 'done', passportId: passport.id } : f)),
            passports: [...state.passports, passport],
            originalPassports: { ...state.originalPassports, [passport.id]: { ...passport } },
          }));
        } catch (error: unknown) {
          const message =
            axios.isAxiosError(error)
              ? String(error.response?.data?.message ?? error.message ?? 'Ошибка загрузки файла')
              : 'Ошибка загрузки файла';

          set((state) => ({
            files: state.files.map((f) => (f.id === fileId ? { ...f, status: 'error', errorMessage: message } : f)),
            uploadError: message,
          }));
        }
      }

      set({ isUploading: false });
    },

    exportSelectedToExcel: async (deleteAfterExport) => {
      const { selectedIds, passports } = get();
      if (!selectedIds.length) {
        set({ exportError: 'Выберите хотя бы одну карточку для экспорта.' });
        return;
      }
      const selectedSet = new Set(selectedIds);
      const rows = passports.filter((p) => selectedSet.has(p.id));

      set({ isExporting: true, exportError: null });

      try {
        const sheetRows = rows.map((row, index) => ({
          '№': index + 1,
          'ID': row.id,
          'Наименование оборудования': row.equipment_name,
          'Назначение': row.purpose,
          'Тех. характеристики': row.technical_specs,
          'Изготовитель': row.manufacturer,
          'Нормативные документы': row.normative_docs,
          'Номер паспорта': row.passport_number,
          'Дата выдачи': row.issue_date,
          'Комплектность': row.completeness,
          'Срок службы': row.service_life,
          'Гарантия': row.warranty,
          'Файл-источник': row.sourceFile ?? '',
        }));

        const worksheet = XLSX.utils.json_to_sheet(sheetRows);
        worksheet['!cols'] = [
          { wch: 6 },  // №
          { wch: 20 }, // ID
          { wch: 36 }, // Наименование оборудования
          { wch: 24 }, // Назначение
          { wch: 28 }, // Тех. характеристики
          { wch: 28 }, // Изготовитель
          { wch: 26 }, // Нормативные документы
          { wch: 20 }, // Номер паспорта
          { wch: 14 }, // Дата выдачи
          { wch: 22 }, // Комплектность
          { wch: 16 }, // Срок службы
          { wch: 14 }, // Гарантия
          { wch: 30 }, // Файл-источник
        ];

        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, 'Паспорта');
        const excelBuffer = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });

        const fileName = `passports_export_${new Date().toISOString().slice(0, 10)}.xlsx`;
        const blob = new Blob([excelBuffer], {
          type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        });
        const objectUrl = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = objectUrl;
        link.download = fileName;
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(objectUrl);

        if (deleteAfterExport) {
          set((state) => {
            const nextPassports = state.passports.filter((p) => !selectedSet.has(p.id));
            const nextOriginal: Record<string, PassportRow> = {};
            nextPassports.forEach((p) => {
              nextOriginal[p.id] = state.originalPassports[p.id] ?? { ...p };
            });
            return {
              passports: nextPassports,
              originalPassports: nextOriginal,
              selectedIds: [],
              selectAll: false,
            };
          });
        }
      } catch (error: unknown) {
        const message = String((error as Error)?.message ?? 'Ошибка экспорта в Excel');
        set({ exportError: message });
      } finally {
        set({ isExporting: false });
      }
    },
  };
});

export default useStore;
