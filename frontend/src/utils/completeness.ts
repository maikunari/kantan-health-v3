import { Provider } from '../types';

export interface CompletenessResult {
  percentage: number;
  completed: number;
  total: number;
  missingFields: string[];
  completedFields: string[];
}

export interface FieldGroup {
  key: string;
  label: string;
  fields: string[];
  weight: number; // How important this group is (1-3)
}

// Standardized field groups for completeness calculation
export const COMPLETENESS_FIELD_GROUPS: FieldGroup[] = [
  {
    key: 'basic',
    label: 'Basic Information',
    fields: ['provider_name', 'address', 'city', 'phone'],
    weight: 3
  },
  {
    key: 'location',
    label: 'Location Data',
    fields: ['latitude', 'longitude'],
    weight: 2
  },
  {
    key: 'content',
    label: 'AI Content',
    fields: ['ai_description', 'seo_title', 'seo_description'],
    weight: 2
  },
  {
    key: 'contact',
    label: 'Contact Information',
    fields: ['website'],
    weight: 1
  },
  {
    key: 'medical',
    label: 'Medical Information',
    fields: ['specialties', 'english_proficiency_score'],
    weight: 2
  },
  {
    key: 'accessibility',
    label: 'Accessibility',
    fields: ['wheelchair_accessible'],
    weight: 1
  }
];

/**
 * Calculate provider completeness using standardized field groups
 */
export function calculateProviderCompleteness(provider: Provider): CompletenessResult {
  let totalWeight = 0;
  let completedWeight = 0;
  const missingFields: string[] = [];
  const completedFields: string[] = [];
  
  COMPLETENESS_FIELD_GROUPS.forEach(group => {
    group.fields.forEach(fieldName => {
      const value = getFieldValue(provider, fieldName);
      const isComplete = isFieldComplete(fieldName, value);
      
      totalWeight += group.weight;
      
      if (isComplete) {
        completedWeight += group.weight;
        completedFields.push(fieldName);
      } else {
        missingFields.push(fieldName);
      }
    });
  });
  
  const percentage = totalWeight > 0 ? Math.round((completedWeight / totalWeight) * 100) : 0;
  
  return {
    percentage,
    completed: completedFields.length,
    total: completedFields.length + missingFields.length,
    missingFields,
    completedFields
  };
}

/**
 * Calculate completeness for a specific field group
 */
export function calculateGroupCompleteness(provider: Provider, groupKey: string): CompletenessResult {
  const group = COMPLETENESS_FIELD_GROUPS.find(g => g.key === groupKey);
  if (!group) {
    return { percentage: 0, completed: 0, total: 0, missingFields: [], completedFields: [] };
  }
  
  const missingFields: string[] = [];
  const completedFields: string[] = [];
  
  group.fields.forEach(fieldName => {
    const value = getFieldValue(provider, fieldName);
    const isComplete = isFieldComplete(fieldName, value);
    
    if (isComplete) {
      completedFields.push(fieldName);
    } else {
      missingFields.push(fieldName);
    }
  });
  
  const percentage = group.fields.length > 0 
    ? Math.round((completedFields.length / group.fields.length) * 100) 
    : 0;
  
  return {
    percentage,
    completed: completedFields.length,
    total: group.fields.length,
    missingFields,
    completedFields
  };
}

/**
 * Get the completion status color based on percentage
 */
export function getCompletenessColor(percentage: number): string {
  if (percentage >= 90) return '#52c41a'; // Green
  if (percentage >= 70) return '#faad14'; // Yellow
  if (percentage >= 50) return '#fa8c16'; // Orange
  return '#f5222d'; // Red
}

/**
 * Get the completion status text
 */
export function getCompletenessStatus(percentage: number): 'success' | 'normal' | 'exception' {
  if (percentage >= 90) return 'success';
  if (percentage >= 70) return 'normal';
  return 'exception';
}

/**
 * Get field value from provider object, handling nested paths
 */
function getFieldValue(provider: Provider, fieldName: string): any {
  const parts = fieldName.split('.');
  let value: any = provider;
  
  for (const part of parts) {
    value = value?.[part];
  }
  
  return value;
}

/**
 * Check if a field is considered complete
 */
function isFieldComplete(fieldName: string, value: any): boolean {
  // Handle null/undefined
  if (value === null || value === undefined) {
    return false;
  }
  
  // Handle empty strings
  if (typeof value === 'string' && value.trim() === '') {
    return false;
  }
  
  // Handle empty arrays
  if (Array.isArray(value) && value.length === 0) {
    return false;
  }
  
  // Handle empty objects
  if (typeof value === 'object' && !Array.isArray(value) && Object.keys(value).length === 0) {
    return false;
  }
  
  // Special cases for specific fields
  switch (fieldName) {
    case 'english_proficiency_score':
      return typeof value === 'number' && value > 0;
    
    case 'latitude':
    case 'longitude':
      return typeof value === 'number' && !isNaN(value);
    
    case 'specialties':
      return Array.isArray(value) ? value.length > 0 : (typeof value === 'string' && value.trim() !== '');
    
    default:
      return true; // Field has some value
  }
}

/**
 * Get a human-readable field label
 */
export function getFieldLabel(fieldName: string): string {
  const fieldLabels: Record<string, string> = {
    'provider_name': 'Provider Name',
    'address': 'Address',
    'city': 'City',
    'phone': 'Phone Number',
    'website': 'Website',
    'latitude': 'Latitude',
    'longitude': 'Longitude',
    'ai_description': 'AI Description',
    'seo_title': 'SEO Title',
    'seo_description': 'SEO Description',
    'specialties': 'Medical Specialties',
    'english_proficiency_score': 'English Proficiency',
    'wheelchair_accessible': 'Wheelchair Access'
  };
  
  return fieldLabels[fieldName] || fieldName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}