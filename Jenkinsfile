pipeline {
    agent any

    parameters {
        string(name: 'SERVER_IP', defaultValue: '192.168.110.134', description: 'Target deployment server IP address')
        credentials(
            name: 'DEPLOY_SSH_CREDENTIALS_ID',
            defaultValue: 'ztp_server',
            description: 'Jenkins SSH private key credentials for the deployment server',
            credentialType: 'com.cloudbees.jenkins.plugins.sshcredentials.impl.BasicSSHUserPrivateKey',
            required: true
        )
    }

    environment {
        IMAGE_NAME='gyao1123/ztp-controller'
        CONTAINER_NAME = 'test' 
        HOST_PORT = '8000' 
        CONTAINER_PORT = '8000'
    }

    stages {
        stage('generate image tag') {
            steps{
                script {
                    env.IMAGE_TAG = sh(
                        script: "date +%Y%m%d-%H%M%S", 
                        returnStdout: true
                    ).trim()
                }
            }
        }

        stage('checkout') {
            steps {
                checkout scm
            }
        }

        stage('build docker image') {
            steps{    
                sh '''
                docker build -t $IMAGE_NAME:$IMAGE_TAG .
                docker tag $IMAGE_NAME:$IMAGE_TAG $IMAGE_NAME:latest
                '''
            }
        }

        stage('push docker image'){
            steps{
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub_token',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh '''
                    echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                    docker push $IMAGE_NAME:$IMAGE_TAG
                    docker push $IMAGE_NAME:latest
                    '''
                }
            }
        }

        stage('deploy to server'){
            steps{
                script {
                    if (!params.SERVER_IP?.trim()) {
                        error('SERVER_IP parameter is required')
                    }
                    if (!params.DEPLOY_SSH_CREDENTIALS_ID?.trim()) {
                        error('DEPLOY_SSH_CREDENTIALS_ID parameter is required')
                    }
                }
                withCredentials([sshUserPrivateKey(
                    credentialsId: params.DEPLOY_SSH_CREDENTIALS_ID,
                    keyFileVariable: 'DEPLOY_SSH_KEY',
                    usernameVariable: 'DEPLOY_USER'
                )]) {
                    sh '''
                    ssh -i "$DEPLOY_SSH_KEY" -o StrictHostKeyChecking=no "$DEPLOY_USER@$SERVER_IP" "
                        set -e
                        docker pull $IMAGE_NAME:$IMAGE_TAG
                        docker rm -f $CONTAINER_NAME || true
                        docker run -d --name $CONTAINER_NAME \
                            --restart unless-stopped \
                            -p $HOST_PORT:$CONTAINER_PORT \
                            $IMAGE_NAME:$IMAGE_TAG
                    "
                    '''
                }
            }
        }



    }

    post{
        always{
            sh '''
            docker rmi $IMAGE_NAME:$IMAGE_TAG || true
            docker rmi $IMAGE_NAME:latest || true
            '''
        }
    }

}
