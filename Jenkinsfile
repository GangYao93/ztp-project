pipeline {
    agent any

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