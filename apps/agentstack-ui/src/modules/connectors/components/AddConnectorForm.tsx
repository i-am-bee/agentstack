import { useForm } from 'react-hook-form';

export interface CreateConnectorForm {
  client_id?: string;
  client_secret?: string;
  url: string;
}

interface AddConnectorFormProps {
  isPending: boolean;
  onSubmit: (data: CreateConnectorForm) => void;
}

export const AddConnectorForm = (props: AddConnectorFormProps) => {
  const {
    handleSubmit,
    register,
    getValues,
    formState: { errors },
  } = useForm<CreateConnectorForm>();

  return (
    <form onSubmit={handleSubmit(props.onSubmit)}>
      <input type="text" placeholder="URL" {...register('url', { required: true })} />
      <input type="text" placeholder="Client ID" {...register('client_id')} />
      <input
        type="text"
        placeholder="Client Secret"
        {...register('client_secret', {
          validate: (value) => {
            const currentClientId = getValues('client_id');
            if (!currentClientId || currentClientId.trim() === '') {
              return !value || value.trim() === '' || 'Client secret must be empty when client ID is empty';
            }
            return true;
          },
        })}
      />
      {errors.client_secret && <span style={{ color: 'red' }}>{errors.client_secret.message}</span>}
      <button type="submit" disabled={props.isPending}>
        {props.isPending ? 'Adding...' : 'Add Connector'}
      </button>
    </form>
  );
};
