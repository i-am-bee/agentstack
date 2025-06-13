# SeaweedFS Integration

This document describes the integration of SeaweedFS as a subchart dependency in the BeeAI Platform Helm chart.

## Changes Made

1. Added SeaweedFS as a subchart dependency in `Chart.yaml`:
   ```yaml
   - condition: seaweedfs.enabled
     name: seaweedfs
     repository: https://seaweedfs.github.io/seaweedfs/helm
     version: 3.x.x
   ```

2. Added SeaweedFS configuration in `values.yaml`:
   ```yaml
   ## SeaweedFS chart configuration
   seaweedfs:
     enabled: true
     fullnameOverride: "seaweedfs"
     master:
       replicas: 1
       resources:
         requests:
           memory: 128Mi
     volume:
       replicas: 1
       resources:
         requests:
           memory: 128Mi
     filer:
       replicas: 1
       resources:
         requests:
           memory: 128Mi
     s3:
       enabled: true
       replicas: 1
       resources:
         requests:
           memory: 128Mi
       port: 8333
       accessKey: "minioadmin"
       secretKey: "minioadmin"

   ## External SeaweedFS configuration
   externalSeaweedFS:
     endpoint: "http://minio:9000"
     accessKey: "minioadmin"
     secretKey: "minioadmin"
     bucketName: "beeai-files"
     region: "us-east-1"
     secure: false
   ```

3. Updated `deployment.yaml` to add environment variables for SeaweedFS configuration:
   ```yaml
   # Object Storage Configuration
   {{- if .Values.seaweedfs.enabled }}
   - name: OBJECT_STORAGE__ENDPOINT_URL
     value: "http://{{ .Release.Name }}-seaweedfs-s3:{{ .Values.seaweedfs.s3.port }}"
   - name: OBJECT_STORAGE__ACCESS_KEY
     value: {{ .Values.seaweedfs.s3.accessKey | quote }}
   - name: OBJECT_STORAGE__SECRET_KEY
     value: {{ .Values.seaweedfs.s3.secretKey | quote }}
   - name: OBJECT_STORAGE__BUCKET_NAME
     value: "beeai-files"
   - name: OBJECT_STORAGE__REGION
     value: "us-east-1"
   - name: OBJECT_STORAGE__SECURE
     value: "false"
   {{- else }}
   - name: OBJECT_STORAGE__ENDPOINT_URL
     value: {{ .Values.externalSeaweedFS.endpoint | quote }}
   - name: OBJECT_STORAGE__ACCESS_KEY
     value: {{ .Values.externalSeaweedFS.accessKey | quote }}
   - name: OBJECT_STORAGE__SECRET_KEY
     value: {{ .Values.externalSeaweedFS.secretKey | quote }}
   - name: OBJECT_STORAGE__BUCKET_NAME
     value: {{ .Values.externalSeaweedFS.bucketName | quote }}
   - name: OBJECT_STORAGE__REGION
     value: {{ .Values.externalSeaweedFS.region | quote }}
   - name: OBJECT_STORAGE__SECURE
     value: {{ .Values.externalSeaweedFS.secure | quote }}
   {{- end }}
   ```

## Testing

To test this integration:

1. Update the Helm dependencies:
   ```bash
   helm dependency update ./helm/beeai-platform
   ```

2. Install or upgrade the Helm chart:
   ```bash
   helm upgrade --install beeai-platform ./helm/beeai-platform
   ```

3. Verify that the SeaweedFS pods are running:
   ```bash
   kubectl get pods | grep seaweedfs
   ```

4. Test file upload and retrieval using the BeeAI Platform API.

## Configuration Options

### Using the Embedded SeaweedFS

By default, the chart will deploy SeaweedFS as a subchart. You can customize the SeaweedFS configuration in the `values.yaml` file under the `seaweedfs` section.

### Using an External S3-Compatible Storage

If you want to use an external S3-compatible storage instead of the embedded SeaweedFS, set `seaweedfs.enabled` to `false` and configure the external storage in the `externalSeaweedFS` section:

```yaml
seaweedfs:
  enabled: false

externalSeaweedFS:
  endpoint: "https://your-s3-endpoint"
  accessKey: "your-access-key"
  secretKey: "your-secret-key"
  bucketName: "your-bucket"
  region: "your-region"
  secure: true
```